"""Pydantic schemas for EchoMind audio intelligence data structures."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TranscriptSegment(BaseModel):
    """Represents a single segment/turn of transcribed speech."""
    id: int
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    speaker: str = Field(default="Speaker 1", description="Speaker identifier")
    text: str = Field(..., description="Transcribed text")


class TranscriptResult(BaseModel):
    """Complete transcription output with metadata."""
    segments: List[TranscriptSegment] = Field(default_factory=list)
    full_text: str = Field(default="")
    language: str = Field(default="id", description="Detected language code")
    language_probability: float = Field(default=0.0)
    duration_seconds: float = Field(default=0.0)


class ActionItem(BaseModel):
    """Structured action item extracted from conversation."""
    task: str = Field(..., description="Actionable task or assignment")
    pic: str = Field(default="Unassigned", description="Person in charge / Assignee")
    deadline: str = Field(default="TBD", description="Target completion date or timeframe")
    priority: str = Field(default="Medium", description="High, Medium, or Low")
    context: Optional[str] = Field(default=None, description="Relevant context or background")


class SentimentMoment(BaseModel):
    """Specific moment in conversation with notable sentiment."""
    timestamp: str = Field(..., description="e.g. 02:15")
    tone: str = Field(..., description="e.g. Optimistic, Critical, Hesitant, Enthusiastic")
    quote: str = Field(..., description="Excerpt from speaker")


class MeetingInsight(BaseModel):
    """Complete structured intelligence report."""
    title: str = Field(default="Ringkasan Pertemuan")
    executive_summary: str = Field(default="")
    key_topics: List[str] = Field(default_factory=list)
    action_items: List[ActionItem] = Field(default_factory=list)
    overall_sentiment: str = Field(default="Neutral", description="Positive, Neutral, or Constructive/Tense")
    sentiment_score: float = Field(default=0.0, description="Scale from -1.0 (very negative) to +1.0 (very positive)")
    key_moments: List[SentimentMoment] = Field(default_factory=list)
    decisions_made: List[str] = Field(default_factory=list)
