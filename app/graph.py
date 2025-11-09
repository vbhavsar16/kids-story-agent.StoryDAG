# app/graph.py
from langgraph.graph import StateGraph, END
from .nodes import (
    classify_node, extract_constraints_node, plan_node, storyteller_node,
    judge_node, revise_node, finalize_node
)

def build_graph():
    g = StateGraph(dict)

    g.add_node("classify_step", classify_node)
    g.add_node("extract_step", extract_constraints_node)
    g.add_node("plan_step", plan_node)
    g.add_node("tell_step", storyteller_node)
    g.add_node("judge_step", judge_node)
    g.add_node("revise_step", revise_node)
    g.add_node("finalize_step", finalize_node)

    g.set_entry_point("classify_step")
    g.add_edge("classify_step", "extract_step")
    g.add_edge("extract_step", "plan_step")
    g.add_edge("plan_step", "tell_step")
    g.add_edge("tell_step", "judge_step")

    # Single-pass policy:
    # OK -> finalize; else -> one revise; then always finalize
    def should_pass(state: dict):
        rep = state.get("judge_report", {})
        scores = rep.get("scores", {})
        ok = (
            scores.get("safety") == 5
            and scores.get("faithfulness", 0) >= 4
            and all(
                scores.get(k, 0) >= 4
                for k in [
                    "instruction_adherence",
                    "age_fit",
                    "bedtime_tone",
                    "clarity",
                    "arc",
                    "engagement",
                ]
            )
        )
        return "finalize" if ok else "revise"

    g.add_conditional_edges("judge_step", should_pass, {
        "finalize": "finalize_step",
        "revise": "revise_step",
    })

    # No loop back to judge — finalize after one revise
    g.add_edge("revise_step", "finalize_step")

    g.add_edge("finalize_step", END)
    return g.compile()
