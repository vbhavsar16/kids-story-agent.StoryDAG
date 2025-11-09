# main.py
import os, textwrap
from dotenv import load_dotenv
from app.graph import build_graph
from app.nodes import judge_node, feedback_revise, finalize_node

load_dotenv()

def print_scores(report):
    s = report["scores"]
    print("\nJUDGE SCORES (0–5)")
    for k in ["faithfulness","instruction_adherence","age_fit","safety","bedtime_tone","clarity","arc","engagement"]:
        if k in s:
            print(f"  {k:20s}: {s[k]}")
    print("  verdict              :", report["verdict"])
    if report.get("required_fixes"):
        print("  required_fixes:")
        for f in report["required_fixes"]:
            print("   -", f)
    if report.get("keep_strengths"):
        print("  keep_strengths:")
        for k in report["keep_strengths"]:
            print("   -", k)


def run_once(user_request: str):
    graph = build_graph()
    state = {"user_request": user_request, "revise_count": 0}
    # No recursion limit needed now; graph is DAG
    state = graph.invoke(state)
    return state


def main():
    print("Welcome to the Bedtime Story Agent ✨ (ages 5–10)")
    user_request = input("What kind of story do you want to hear? ").strip()
    if not user_request:
        user_request = "A cosy story about a shy firefly who learns to glow with a friend."

    # First pass
    state = run_once(user_request)

    print("\n" + "-"*70)
    print("\nFINAL STORY (v1)\n")
    print(textwrap.fill(state["final_story"], width=92))
    print("\n" + "-"*70)

    # Re-judge the FINAL story
    state["draft_story"] = state["final_story"]
    state = judge_node(state)
    print_scores(state["judge_report"])

    if state["judge_report"].get("metrics"):
        print("\nOBJECTIVE METRICS")
        for k, v in state["judge_report"]["metrics"].items():
            print(f"  {k:18s}: {v}")

    # Feedback turn
    print("\nWould you like any changes? (e.g., 'make it shorter', 'add a friendly owl', 'more rhyme')")
    fb = input("Your feedback (or press Enter to skip): ").strip()
    if fb:
        state = feedback_revise(state, fb)
        state = finalize_node(state)

        print("\n" + "-"*70)
        print("\nFINAL STORY (v2, after feedback)\n")
        print(textwrap.fill(state["final_story"], width=92))
        print("\n" + "-"*70)

        state["draft_story"] = state["final_story"]
        state = judge_node(state)
        print_scores(state["judge_report"])

if __name__ == "__main__":
    main()
