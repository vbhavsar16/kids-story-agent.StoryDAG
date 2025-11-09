# app/nodes.py
import os, json
from openai import OpenAI
from .prompts import (
    CLASSIFIER_PROMPT, EXTRACT_PROMPT, PLANNER_PROMPT, STORYTELLER_PROMPT,
    JUDGE_PROMPT, REVISER_PROMPT, FEEDBACK_REVISER_PROMPT
)
from .utils import extract_json, with_goodnight, force_list, coerce_int
from .safety import unsafe
from .metrics import compute_metrics


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-3.5-turbo"  # do not change

def _chat(prompt: str, temperature=0.6, max_tokens=700) -> str:
    res = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens
    )
    return res.choices[0].message.content.strip()

def classify_node(state: dict) -> dict:
    raw = _chat(CLASSIFIER_PROMPT.format(user_request=state["user_request"]), temperature=0.2, max_tokens=300)
    data = extract_json(raw)
    # default intended_use if missing
    if "intended_use" not in data:
        # heuristics: if 'not a bedtime' present, general; else bedtime
        iu = "general" if "not a bedtime" in state["user_request"].lower() else "bedtime"
        data["intended_use"] = iu
    state["classification"] = data
    return state

# NEW: constraint extractor
def extract_constraints_node(state: dict) -> dict:
    raw = _chat(EXTRACT_PROMPT.format(user_request=state["user_request"]), temperature=0.1, max_tokens=300)
    cons = extract_json(raw)
    # Ensure lists
    cons["must_include"] = force_list(cons.get("must_include"))
    cons["setting_hints"] = force_list(cons.get("setting_hints"))
    cons["style_hints"] = force_list(cons.get("style_hints"))
    # If classifier flagged red flags, we can add "soften" style hint
    if state["classification"].get("red_flags"):
        cons["style_hints"].append("soften any intense content")
    # If user didn't specify, carry obvious tokens
    if not cons["must_include"]:
        # naive keyword fallback
        cons["must_include"] = []
    state["constraints"] = cons
    return state

def plan_node(state: dict) -> dict:
    cls = state["classification"]
    cons = state["constraints"]
    mood = cls.get("mood", "soothing")
    if cls.get("red_flags"):
        mood = "very-soothing"
    raw = _chat(PLANNER_PROMPT.format(
        category=cls.get("category","custom"),
        mood=mood,
        intended_use=cls.get("intended_use","bedtime"),
        must_include=cons["must_include"],
        setting_hints=cons["setting_hints"],
        style_hints=cons["style_hints"]
    ), temperature=0.4, max_tokens=700)
    beats = extract_json(raw)

    # --- normalize word_limit to int
    wl = beats.get("word_limit", 500)
    beats["word_limit"] = coerce_int(wl, default=500)

    state["plan"] = beats
    return state

def storyteller_node(state: dict) -> dict:
    beats_json = json.dumps(state["plan"], ensure_ascii=False, indent=2)
    cls = state["classification"]
    cons = state["constraints"]
    story = _chat(STORYTELLER_PROMPT.format(
        beats_json=beats_json,
        intended_use=cls.get("intended_use","bedtime"),
        must_include=cons["must_include"],
        word_limit=state["plan"]["word_limit"]
    ), temperature=0.8, max_tokens=1000)
    if unsafe(story):
        story = _chat(
            REVISER_PROMPT.format(
                fixes="['Remove any frightening element. Soften imagery.']",
                strengths="[]",
                intended_use=cls.get("intended_use","bedtime"),
                must_include=cons["must_include"],
                story=story
            ),
            temperature=0.5, max_tokens=900
        )
    state["draft_story"] = story.strip()
    return state

def judge_node(state: dict) -> dict:
    cls = state["classification"]
    cons = state["constraints"]
    intended = cls.get("intended_use","bedtime")
    limit = coerce_int(state["plan"].get("word_limit", 500), default=500)
    metrics = compute_metrics(
        story=state["draft_story"],
        must_include=cons["must_include"],
        intended_use=intended,
        word_limit=limit
    )

    raw = _chat(JUDGE_PROMPT.format(
        story=state["draft_story"],
        intended_use=intended,
        must_include=cons["must_include"],
        metrics=json.dumps(metrics, ensure_ascii=False, indent=2)
    ), temperature=0.0, max_tokens=900)

    data = extract_json(raw)
    # normalize arrays
    data["keep_strengths"] = force_list(data.get("keep_strengths"))
    data["required_fixes"] = force_list(data.get("required_fixes"))
    # coerce numeric scores
    if isinstance(data.get("scores"), dict):
        for k in ["faithfulness","instruction_adherence","age_fit","safety","bedtime_tone","clarity","arc","engagement"]:
            v = data["scores"].get(k)
            if isinstance(v, str) and v.isdigit():
                data["scores"][k] = int(v)
            elif isinstance(v, float):
                data["scores"][k] = int(round(v))
    else:
        data["scores"] = {}

    # --- Calibrate/clip using objective metrics (guard against rubber-stamp 5s)
    s = data["scores"]
    s.setdefault("faithfulness", 3)
    s.setdefault("instruction_adherence", 3)
    s.setdefault("age_fit", 3)
    s.setdefault("safety", 5)          # assume safe unless flagged elsewhere
    s.setdefault("bedtime_tone", 4)
    s.setdefault("clarity", 4)
    s.setdefault("arc", 4)
    s.setdefault("engagement", 4)

    if metrics["missing_must_include"]:
        s["faithfulness"] = min(s["faithfulness"], 3)
        data["required_fixes"].append(f"Explicitly include: {metrics['missing_must_include']}.")

    if metrics["over_word_limit"] or metrics["dialogue_over_2"]:
        s["instruction_adherence"] = min(s["instruction_adherence"], 3)
        if metrics["over_word_limit"]:
            data["required_fixes"].append("Trim to word limit.")
        if metrics["dialogue_over_2"]:
            data["required_fixes"].append("Keep dialogue to at most 2 short lines.")

    if metrics["coleman_liau_index"] > 4.0 or metrics["avg_sentence_len"] > 15:
        s["age_fit"] = min(s["age_fit"], 3)
        data["required_fixes"].append("Shorten sentences and simplify words.")

    if intended == "bedtime" and not metrics["bedtime_tail_ok"]:
        s["bedtime_tone"] = min(s["bedtime_tone"], 3)
        data["required_fixes"].append("End with a cozy goodnight image/line.")

    # verdict rule
    pass_ok = (
        s.get("safety", 0) == 5 and
        s.get("faithfulness", 0) >= 4 and
        all(s.get(k, 0) >= 4 for k in ["instruction_adherence","age_fit","bedtime_tone","clarity","arc","engagement"])
    )
    data["verdict"] = "pass" if pass_ok else "revise"

    # attach metrics for transparency (optional)
    data["metrics"] = metrics

    state["judge_report"] = data
    return state


def revise_node(state: dict) -> dict:
    fixes = json.dumps(state["judge_report"].get("required_fixes", []), ensure_ascii=False)
    strengths = json.dumps(state["judge_report"].get("keep_strengths", []), ensure_ascii=False)
    revised = _chat(
        REVISER_PROMPT.format(
            fixes=fixes,
            strengths=strengths,
            intended_use=state["classification"].get("intended_use","bedtime"),
            must_include=state["constraints"]["must_include"],
            story=state["draft_story"],
        ),
        temperature=0.5,
        max_tokens=1000,
    )
    before = state["draft_story"]
    state["draft_story"] = revised.strip()
    # debug/telemetry only
    state["revise_count"] = int(state.get("revise_count", 0)) + 1
    # if no change, we still finalize next (graph is acyclic now)
    return state


def finalize_node(state: dict) -> dict:
    # Only append a goodnight tail for bedtime
    if state["classification"].get("intended_use","bedtime") == "bedtime":
        state["final_story"] = with_goodnight(state["draft_story"])
    else:
        state["final_story"] = state["draft_story"].strip()
    return state

def feedback_revise(state: dict, feedback: str) -> dict:
    cls = state["classification"]
    cons = state["constraints"]
    fixes = json.dumps(state.get("judge_report", {}).get("required_fixes", []), ensure_ascii=False)
    strengths = json.dumps(state.get("judge_report", {}).get("keep_strengths", []), ensure_ascii=False)
    revised = _chat(FEEDBACK_REVISER_PROMPT.format(
        feedback=feedback,
        fixes=fixes,
        strengths=strengths,
        intended_use=cls.get("intended_use","bedtime"),
        must_include=cons["must_include"],
        story=state.get("final_story") or state.get("draft_story","")
    ), temperature=0.5, max_tokens=1000)
    state["draft_story"] = revised.strip()
    state["revise_count"] = int(state.get("revise_count", 0)) + 1
    return state
