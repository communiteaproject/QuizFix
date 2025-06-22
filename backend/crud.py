from typing import List, Optional

from sqlmodel import Session, select

from backend.models import (
    AnswerSubmission,
    Game,
    GamePhase,
    Question,
    Round,
    Team,
    User,
    UserRole,
)


# Game operations

def create_game(session: Session, title: str) -> Game:
    game = Game(title=title)
    session.add(game)
    session.commit()
    session.refresh(game)

    # Create six rounds by default
    for idx in range(1, 7):
        round_ = Round(game_id=game.id, number=idx)
        session.add(round_)
    session.commit()
    return game


def get_game(session: Session, game_id: int) -> Optional[Game]:
    return session.get(Game, game_id)


def set_game_phase(session: Session, game: Game, phase: GamePhase) -> Game:
    game.phase = phase
    session.add(game)
    session.commit()
    session.refresh(game)
    return game


# Team operations

def create_team(session: Session, name: str) -> Team:
    team = Team(name=name)
    session.add(team)
    session.commit()
    session.refresh(team)
    return team


def list_teams(session: Session) -> List[Team]:
    return session.exec(select(Team)).all()


# User operations

def create_user(session: Session, name: str, role: UserRole, team_id: Optional[int] = None) -> User:
    user = User(name=name, role=role, team_id=team_id)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def list_users(session: Session) -> List[User]:
    return session.exec(select(User)).all()


# Question operations

def create_question(
    session: Session,
    round_id: int,
    order: int,
    text: str,
    answer: str,
    media_url: Optional[str] = None,
) -> Question:
    question = Question(
        round_id=round_id,
        order=order,
        text=text,
        answer=answer,
        media_url=media_url,
    )
    session.add(question)
    session.commit()
    session.refresh(question)
    return question


def list_questions_for_round(session: Session, round_id: int) -> List[Question]:
    return session.exec(select(Question).where(Question.round_id == round_id).order_by(Question.order)).all()


def update_question(session: Session, question_id: int, **fields) -> Question:
    question = session.get(Question, question_id)
    if not question:
        raise ValueError("Question not found")
    for key, value in fields.items():
        if hasattr(question, key) and value is not None:
            setattr(question, key, value)
    session.add(question)
    session.commit()
    session.refresh(question)
# Answer operations

def submit_answer(
    session: Session,
    question_id: int,
    team_id: int,
    answer_text: str,
) -> AnswerSubmission:
    submission = AnswerSubmission(
        question_id=question_id,
        team_id=team_id,
        answer_text=answer_text,
    )
    session.add(submission)

    # Mark correctness
    question = session.get(Question, question_id)
    if question and question.answer.lower().strip() == answer_text.lower().strip():
        submission.is_correct = True
    else:
        submission.is_correct = False

    session.commit()
    session.refresh(submission)
    return submission


def leaderboard_for_game(session: Session, game_id: int):
    """Compute leaderboard as total correct answers per team for the game."""
    query = (
        select(
            Team.id,
            Team.name,
            AnswerSubmission.is_correct,
        )
        .join(AnswerSubmission, AnswerSubmission.team_id == Team.id)
        .join(Question, Question.id == AnswerSubmission.question_id)
        .join(Round, Round.id == Question.round_id)
        .where(Round.game_id == game_id)
    )
    rows = session.exec(query).all()

    points = {}
    for team_id, team_name, is_correct in rows:
        if team_id not in points:
            points[team_id] = {
                "team_name": team_name,
                "points": 0,
            }
        if is_correct:
            points[team_id]["points"] += 1

    leaderboard = sorted(points.items(), key=lambda item: item[1]["points"], reverse=True)
    return leaderboard


# Question helper for host

def list_questions_for_game(session: Session, game_id: int) -> List[Question]:
    query = (
        select(Question)
        .join(Round, Round.id == Question.round_id)
        .where(Round.game_id == game_id)
        .order_by(Question.round_id, Question.order)
    )
    return session.exec(query).all()


def set_current_question(session: Session, game: Game, question_id: int):
    game.current_question_id = question_id
    session.add(game)
    session.commit()
    session.refresh(game)
    return game 