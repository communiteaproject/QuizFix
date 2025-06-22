from __future__ import annotations

from enum import Enum
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class UserRole(str, Enum):
    HOST = "host"
    TEAM_MEMBER = "team_member"


class GamePhase(str, Enum):
    GATHERING = "gathering"
    QUESTIONS_PHASE_1 = "questions_phase_1"
    ANSWERS_PHASE_1 = "answers_phase_1"
    LEADERBOARD_PHASE_1 = "leaderboard_phase_1"
    QUESTIONS_PHASE_2 = "questions_phase_2"
    ANSWERS_PHASE_2 = "answers_phase_2"
    LEADERBOARD_PHASE_2 = "leaderboard_phase_2"
    FINISHED = "finished"


class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, nullable=False)

    # Relationships
    members: List["User"] = Relationship(back_populates="team")
    submissions: List["AnswerSubmission"] = Relationship(back_populates="team")


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    role: UserRole

    team_id: Optional[int] = Field(default=None, foreign_key="team.id")
    team: Optional[Team] = Relationship(back_populates="members")


class Game(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    phase: GamePhase = Field(default=GamePhase.GATHERING, nullable=False)

    rounds: List["Round"] = Relationship(back_populates="game")

    current_question_id: Optional[int] = Field(default=None, foreign_key="question.id")
    current_question: Optional["Question"] = Relationship()


class Round(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    game_id: int = Field(foreign_key="game.id")
    number: int  # 1-6

    game: Game = Relationship(back_populates="rounds")
    questions: List["Question"] = Relationship(back_populates="round")


class Question(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    round_id: int = Field(foreign_key="round.id")
    order: int  # 1-10
    text: str
    answer: str
    media_url: Optional[str] = None  # path to image / video on local file system or served URL

    round: Round = Relationship(back_populates="questions")
    submissions: List["AnswerSubmission"] = Relationship(back_populates="question")


class AnswerSubmission(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    question_id: int = Field(foreign_key="question.id")
    team_id: int = Field(foreign_key="team.id")
    answer_text: str
    is_correct: Optional[bool] = None

    question: Question = Relationship(back_populates="submissions")
    team: Team = Relationship(back_populates="submissions") 