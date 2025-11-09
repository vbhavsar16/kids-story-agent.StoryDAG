# app/prompts.py

CLASSIFIER_PROMPT = """You are a story request classifier for a kids-story system.
Input: {user_request}

Return strict JSON with keys:
- category: one of ["animal","friendship","fantasy-gentle","adventure-soft","science-cosy","custom"]
- mood: one of ["very-soothing","soothing","light-playful"]
- intended_use: one of ["bedtime","general"]  (If user says 'not a bedtime story' -> general)
- red_flags: array of unsafe topics (violence, fear, weapons, harm, bullying, nightmares, mature themes)
Only output JSON. No extra text.
"""

# NEW: extract hard constraints from the request
EXTRACT_PROMPT = """Extract constraints from the user's request.

Input: {user_request}

Return strict JSON with:
- must_include: array of short strings that must appear in the story (e.g., "king", "queen", "lost everything")
- setting_hints: array of short hints (e.g., "castle", "village", "forest")
- style_hints: array of short hints about tone or style if given (e.g., "not bedtime", "funny", "soft adventure")

Only JSON. No extra text.
"""

PLANNER_PROMPT = """You are a story planner for ages 5–10.

Constraints:
- Intended use: {intended_use}. If "bedtime", the tone must be calm and sleepy.
- Tone: {mood}. Keep content reassuring and age-appropriate.
- Vocab: common words; short sentences; simple past or present.
- Length target: 350–600 words.
- Arc: 3 acts with soft stakes and a positive ending.
- Category hint: {category}.
- Must include: {must_include}.
- Setting hints: {setting_hints}.
- Style hints: {style_hints}.

Return strict JSON with:
setting, characters (2–3), gentle_problem,
act1, act2, act3, calming_motifs (3–5),
moral, style_knobs (e.g., cadence="lullaby"| "story", repetition="light", dialogue="sprinkle"),
word_limit
"""

STORYTELLER_PROMPT = """You are a kids storyteller (ages 5–10).

Write a complete story from these beats:
{beats_json}

Hard rules:
- Include each of these exactly-once-or-naturally: {must_include}. They must appear in the story.
- Respect intended use: {intended_use}. If bedtime, keep low arousal and end with a cozy image. If general, keep it uplifting and age-safe but not sleepy.
- Simple words. Short sentences (aim ≤15 words).
- No frightening or violent content. No harm.
- Keep within {word_limit} words.
- 1–2 short lines of dialogue total. Friendly names only.
- Subtle moral; no lectures.

Output ONLY the story.
"""

JUDGE_PROMPT = """You are a strict children's story judge for ages 5–10.

You are given OBJECTIVE METRICS (ground truth) and must use them when scoring.
If a metric violates a constraint, deduct points accordingly.

Rubric (integers 0–5):
- faithfulness: includes must_include; follows user premise
- instruction_adherence: obeys word limit, dialogue ≤2, required structure
- age_fit: simple words, short sentences
- safety: no scary/violent/mature themes
- bedtime_tone: if intended_use='bedtime', calm/sleepy; if 'general', tone suitable for kids
- clarity: coherent, easy to follow
- arc: clear begin–middle–end; soft conflict; positive close
- engagement: warm imagery; small delight; not over-exciting

Hard guidance:
- If metrics show missing must_include → faithfulness ≤ 3.
- If over_word_limit or dialogue_over_2 → instruction_adherence ≤ 3.
- If coleman_liau_index > 4.0 or avg_sentence_len > 15 → age_fit ≤ 3.
- Only give a 5 if you can cite at least one concrete evidence phrase from the story for that criterion.

Return JSON:
{{
  "scores": {{
    "faithfulness": 0-5,
    "instruction_adherence": 0-5,
    "age_fit": 0-5,
    "safety": 0-5,
    "bedtime_tone": 0-5,
    "clarity": 0-5,
    "arc": 0-5,
    "engagement": 0-5
  }},
  "required_fixes": ["..."],
  "keep_strengths": ["..."],
  "verdict": "pass" | "revise",
  "evidence": {{
    "faithfulness": ["quoted-or-paraphrased evidence"],
    "instruction_adherence": ["..."],
    "age_fit": ["..."],
    "safety": ["..."],
    "bedtime_tone": ["..."],
    "clarity": ["..."],
    "arc": ["..."],
    "engagement": ["..."]
  }}
}}

OBJECTIVE METRICS (must be respected):
{metrics}

Context:
- intended_use: {intended_use}
- must_include: {must_include}

Story:
---
{story}
---
"""



REVISER_PROMPT = """You are a careful reviser for a children's story.
Apply ONLY these fixes:
{fixes}

Preserve these strengths:
{strengths}

Hard rules:
- Ages 5–10, short sentences, simple words.
- Respect intended use: {intended_use}.
- Include each of: {must_include}.
- No frightening elements.
- Keep length roughly the same; positive ending.

Return ONLY the revised story text.

Original story:
---
{story}
---
"""

FEEDBACK_REVISER_PROMPT = """You are a careful reviser for a children's story.
Apply the user's feedback faithfully, while preserving safety and age-appropriateness.

User feedback:
{feedback}

Also apply these judge fixes if relevant:
{fixes}

Preserve these strengths:
{strengths}

Hard rules:
- Ages 5–10, short sentences, simple words.
- Respect intended use: {intended_use}.
- Include each of: {must_include}.
- End suitably (cozy if bedtime; otherwise positive and gentle).

Return ONLY the revised story text.

Original story:
---
{story}
---
"""
