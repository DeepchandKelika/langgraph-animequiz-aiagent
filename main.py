# main.py
import os
from graph import build_graph
from quizzes import load_quiz_bank

if __name__ == '__main__':
    # load env vars
    from dotenv import load_dotenv; load_dotenv()

    quiz_bank = load_quiz_bank()
    graph = build_graph()
    compiled = graph.compile()
    final = compiled.invoke({
        "quotes": quiz_bank,
        "max_questions": len(quiz_bank),
    })
    print(final["last_output"])