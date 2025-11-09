# StoryDAG

## Deterministic, judge-guided kids’ stories with real metrics and a feedback turn—powered by GPT-3.5-turbo.
1. StoryDAG generates child-appropriate stories by running a deterministic DAG: classify → extract constraints → plan beats → tell → judge (with metrics) → optional revise → finalize.
2. It enforces faithfulness to the user prompt, age fitness (short sentences, simple words), and safety, using measurable checks (word limit, dialogue count, Coleman–Liau readability, required tokens) and an LLM judge. A feedback turn lets users refine tone or content, then the system finalizes—no loops, predictable latency, production-lean.

---

## Key Features

- Acyclic LangGraph DAG (no infinite loops): single-pass revision for predictable latency.
- LLM Judge + Objective Metrics: scores faithfulness, instruction adherence, age-fit, safety, tone, clarity, arc, engagement.
- Constraint Extraction: pulls must_include, setting/style hints from the user’s request to prevent drift.
- Bedtime / General Modes: calm “bedtime” or upbeat “general” stories—your choice.
- Feedback Turn: user critiques → revision → finalize (outside the DAG).
- Strict JSON I/O with drift handling, word-limit coercion, and robust parsing.

---

## Scoring & Metrics

### Judge rubric (0–5 each)
- **faithfulness** — uses `must_include`, follows user premise
- **instruction_adherence** — word limit, ≤2 dialogue lines, structure
- **age_fit** — simple words, short sentences
- **safety** — no scary/violent/mature content
- **bedtime_tone** — calm/sleepy if bedtime; else child-appropriate
- **clarity** — coherent, easy to follow
- **arc** — clear begin–middle–end; soft conflict; positive close
- **engagement** — warm imagery; small delight; not over-exciting

### Objective metrics (ground truth used by judge & code clamps)
- **word count** & `over_word_limit`
- **dialogue lines** & `dialogue_over_2`
- **Coleman–Liau Index** *(readability, no syllable/cmudict dependency)*
- **average sentence length**
- **must_include token coverage**
- **bedtime tail check** *(if bedtime mode)*

> The code **clips scores** when metrics fail (e.g., over word limit ⇒ `instruction_adherence ≤ 3`), so you don’t get unrealistic all-5s.

---

## 🧑‍💻 CLI UX

1. After **v1** is printed, you’ll see **scores + required fixes/strengths**.
2. You can then type a **feedback** message (e.g., “add a friendly owl,” “make it shorter,” “more rhyme”).
3. The system **revises once** and prints **v2**.
