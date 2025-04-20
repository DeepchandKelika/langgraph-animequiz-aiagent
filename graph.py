from langgraph.graph import StateGraph, START, END
from handlers import *

def build_graph()  -> StateGraph:

    graph = StateGraph(QuoteQuizState)

    # Nodes
    graph.add_node("get_next",       get_next_fn)
    graph.add_node("collect_guess",  collect_guess_fn)
    graph.add_node("grade",          grade_node_fn)
    graph.add_node("hint",           hint_fn)
    graph.add_node("summary",        summary_fn)

    # 1. Kick‑off
    graph.add_edge(START, "get_next")

    # 2. Branch out of get_next only via conditional routes:
    graph.add_conditional_edges(
        "get_next",
        end_condition_fn,
        {
            "continue": "collect_guess",  # still more quotes
            "done":     "summary",        # we’re out of quotes
        }
    )

    # 3. collect_guess → grade
    graph.add_edge("collect_guess", "grade")

    # 4. grade → correct vs incorrect
    graph.add_conditional_edges(
        "grade",
        grade_route_fn,
        {"correct": "get_next", "incorrect": "hint"},
    )

    # 5. hint → guess again
    graph.add_edge("hint", "collect_guess")

    # 6. summary → end
    graph.add_edge("summary", END)


    return graph
