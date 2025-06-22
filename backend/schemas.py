from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from backend.models import GamePhase, UserRole


class TeamCreate(BaseModel):
    name: str


class TeamRead(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    name: str
    role: UserRole
    team_id: Optional[int] = None


class UserRead(BaseModel):
    id: int
    name: str
    role: UserRole
    team_id: Optional[int]

    class Config:
        orm_mode = True


class GameCreate(BaseModel):
    title: str


class GameRead(BaseModel):
    id: int
    title: str
    phase: GamePhase

    class Config:
        orm_mode = True


class QuestionCreate(BaseModel):
    text: str
    answer: str
    media_url: Optional[str] = None
    order: int
    round_id: int


class QuestionRead(BaseModel):
    id: int
    text: str
    media_url: Optional[str]
    order: int

    class Config:
        orm_mode = True


class AnswerSubmit(BaseModel):
    question_id: int
    team_id: int
    answer_text: str


class AnswerRead(BaseModel):
    id: int
    question_id: int
    team_id: int
    answer_text: str
    is_correct: Optional[bool]

    class Config:
        orm_mode = True


class LeaderboardEntry(BaseModel):
    team_id: int
    team_name: str
    points: int


class Leaderboard(BaseModel):
    game_id: int
    standings: List[LeaderboardEntry]


class PhaseUpdate(BaseModel):
    phase: GamePhase
    timestamp: datetime = datetime.utcnow()


class CurrentQuestionResponse(BaseModel):
    question: Optional[QuestionRead] 