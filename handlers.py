from state import QuoteQuizState
from google import genai
import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_GENAI_API_KEY"))

chroma_client = chromadb.PersistentClient(path="./anime_vector_db")
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-small-en-v1.5"
)
collection = chroma_client.get_or_create_collection(
    name="anime_bios",
    embedding_function=embedding_fn
)

# Load the next quote (or default to exit)
def get_next_fn(state: QuoteQuizState, **_) -> QuoteQuizState:
    # If we still have questions left to ask
    if state.question_index < state.max_questions:
        # Load the next quote
        idx = state.question_index
        state.current = state.quotes[idx]
        # Prepare for the next round
        state.user_guess = None
        state.hint_used  = False
        state.last_output = f"Quote #{idx+1}: “{state.current['quote']}”"
        # **Advance the index** so next time we get the next quote
        state.question_index += 1
    else:
        # No more quotes: signal the end
        state.current = None
    return state

# Collect the user’s guess
def collect_guess_fn(state: QuoteQuizState, **_) -> QuoteQuizState:
    # Show the current quote stored in last_output
    print(state.last_output)          # e.g.  Quote #1: “I am gonna be the Pirate King!”
    state.user_guess = input("Who said this? ")
    return state

# Grade the guess via Gemini
def grade_node_fn(state: QuoteQuizState, **_) -> QuoteQuizState:
    """Gemini‑powered grading: updates state and returns it."""
    quote  = state.current["quote"]
    answer = state.current["answer"]
    guess  = state.user_guess or ""

    prompt = (
        f"You are an anime trivia grader.\n"
        f"Quote: “{quote}”\n"
        f"Correct Speaker: {answer}\n"
        f"Player’s Guess: {guess}\n\n"
        "1) Reply with 'Correct' if the guess matches the correct speaker.\n"
        "2) Otherwise reply with 'Incorrect' and then 'Hint: <helpful hint>'.\n"
        "Only output those two lines."
    )

    resp = client.models.generate_content(
        model="gemini-2.0-flash-001",
        contents=prompt,
    )

    lines = [l.strip() for l in resp.text.splitlines() if l.strip()]
    is_correct = lines[0].lower().startswith("correct")
    hint = ""
    if not is_correct and len(lines) > 1 and lines[1].lower().startswith("hint:"):
        hint = lines[1].split(":",1)[1].strip()

    if is_correct:
        state.correct_count += 1
        state.last_output   = "✅ Correct!"
    else:
        state.last_output   = f"❌ Nope. Hint: {hint}"

    return state

def grade_route_fn(state: QuoteQuizState, **_) -> str:
    return "correct" if state.last_output.startswith("✅") else "incorrect"


# Show a hint (only once per quote)
def hint_fn(state: QuoteQuizState, **_) -> QuoteQuizState:
    correct_name = state.current["answer"]
    quote = state.current["quote"]

    # RAG: Retrieve matching character bios
    results = collection.query(
        query_texts=[correct_name],
        n_results=1
    )

    context_text = results["documents"][0][0] if results["documents"] else ""

    # Compose prompt using quote + bio
    prompt = (
        f"Quote: \"{quote}\"\n"
        f"Character: {correct_name}\n"
        f"Context: {context_text}\n\n"
        "Give a helpful but not obvious hint that would help a fan guess this character. "
        "Do not mention the character name directly. Keep it under 2 lines."
    )

    response = client.models.generate_content(model="gemini-2.0-flash-001",
        contents=prompt,
        )
    hint = response.text.strip()

    # Update state with hint
    state.last_output = f"💡 Hint: {hint}"
    state.hint_used = True
    return state

# Summarize at the end
def summary_fn(state: QuoteQuizState, **_) -> QuoteQuizState:
    state.last_output = (
        f"Quiz over! You got {state.correct_count}/{state.max_questions} right."
    )
    return state

def end_condition_fn(state: QuoteQuizState, **_) -> str:
    return "done" if state.current is None else "continue"
