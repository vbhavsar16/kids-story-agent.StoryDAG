from pydantic import BaseModel, Field, ValidationError
from typing import List, Dict, Optional

class Classification(BaseModel):
    category: str = Field(description='animal|friendship|fantasy-gentle|adventure-soft|science-cosy|custom')
    mood: str = Field(description='very-soothing|soothing|light-playful')
    red_flags: List[str] = Field(default_factory=list)

class Plan(BaseModel):
    setting: str
    characters: List[str]
    gentle_problem: str
    act1: str
    act2: str
    act3: str
    calming_motifs: List[str]
    moral: str
    style_knobs: Dict[str, str]
    word_limit: int = 500

class Scores(BaseModel):
    age_fit: int
    safety: int
    bedtime_tone: int
    clarity: int
    arc: int
    engagement: int

class JudgeReport(BaseModel):
    scores: Scores
    required_fixes: List[str]
    keep_strengths: List[str]
    verdict: str  # pass|revise

class PipelineState(BaseModel):
    user_request: str
    classification: Optional[Classification] = None
    plan: Optional[Plan] = None
    draft_story: Optional[str] = None
    judge_report: Optional[JudgeReport] = None
    final_story: Optional[str] = None
