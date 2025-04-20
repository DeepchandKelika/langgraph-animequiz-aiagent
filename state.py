from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class QuoteQuizState(BaseModel):
    # question bank: each quote + the correct answer + an optional hint
    quotes: List[Dict[str,str]] = Field(..., description="List of {'quote','answer','hint'}")

    # The current quiz round
    current: Optional[Dict[str,str]] = Field(None, description="The quote currently being asked")
    user_guess: Optional[str] = Field(None, description="User’s guess for the speaker")

    # Tracking
    question_index: int = Field(0, ge=0, description="Which quote we’re on")
    correct_count: int = Field(0, ge=0, description="How many correct so far")
    max_questions: int = Field(..., gt=0, description="Total quotes to ask")

    # For hints & output
    hint_used: bool = Field(False, description="Whether we’ve already shown the hint")
    last_output: Optional[str] = Field(None, description="What to display to the user")
