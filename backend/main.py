from typing import List
import os
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from fastapi.encoders import jsonable_encoder

from backend import crud, models, schemas
from backend.database import get_session, init_db
from backend import wifi

app = FastAPI(title="Local Trivia Game")

origins = [
    "*",  # For local deployment only; you might restrict this in production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HOST_TOKEN = os.environ.get("HOST_TOKEN", "changeme")

MEDIA_DIR = os.environ.get("MEDIA_DIR", "media")
if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR, exist_ok=True)

app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


# Dependency

def get_db_session():
    with get_session() as session:
        yield session


# -- Game endpoints --


@app.post("/games", response_model=schemas.GameRead)
def create_game(game_in: schemas.GameCreate, session: Session = Depends(get_db_session)):
    game = crud.create_game(session, title=game_in.title)
    return game


@app.get("/games/{game_id}", response_model=schemas.GameRead)
def read_game(game_id: int, session: Session = Depends(get_db_session)):
    game = crud.get_game(session, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@app.post("/games/{game_id}/phase", response_model=schemas.GameRead)
async def update_phase(game_id: int, update: schemas.PhaseUpdate, session: Session = Depends(get_db_session)):
    game = crud.get_game(session, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    game = crud.set_game_phase(session, game, update.phase)
    # Broadcast to all connected clients
    await manager.broadcast(
        {
            "type": "phase_update",
            "game_id": game.id,
            "phase": game.phase,
        }
    )
    return game


@app.get("/games", response_model=List[schemas.GameRead])
def list_games(session: Session = Depends(get_db_session)):
    games = session.exec(select(models.Game)).all()
    return games


# -- Team endpoints --


@app.post("/teams", response_model=schemas.TeamRead)
def create_team(team_in: schemas.TeamCreate, session: Session = Depends(get_db_session)):
    team = crud.create_team(session, name=team_in.name)
    return team


@app.get("/teams", response_model=List[schemas.TeamRead])
def list_teams(session: Session = Depends(get_db_session)):
    teams = crud.list_teams(session)
    return teams


# -- User endpoints --


@app.post("/users", response_model=schemas.UserRead)
def create_user(user_in: schemas.UserCreate, session: Session = Depends(get_db_session)):
    user = crud.create_user(
        session,
        name=user_in.name,
        role=user_in.role,
        team_id=user_in.team_id,
    )
    return user


@app.get("/users", response_model=List[schemas.UserRead])
def list_users(session: Session = Depends(get_db_session)):
    users = crud.list_users(session)
    return users


# -- Question endpoints --


@app.post("/questions", response_model=schemas.QuestionRead)
def create_question(question_in: schemas.QuestionCreate, session: Session = Depends(get_db_session)):
    question = crud.create_question(
        session=session,
        round_id=question_in.round_id,
        order=question_in.order,
        text=question_in.text,
        answer=question_in.answer,
        media_url=question_in.media_url,
    )
    return question


@app.get("/rounds/{round_id}/questions", response_model=List[schemas.QuestionRead])
def list_round_questions(round_id: int, session: Session = Depends(get_db_session)):
    return crud.list_questions_for_round(session, round_id)


# -- Answer submission endpoints --


@app.post("/answers", response_model=schemas.AnswerRead)
async def submit_answer(answer_in: schemas.AnswerSubmit, session: Session = Depends(get_db_session)):
    submission = crud.submit_answer(
        session,
        question_id=answer_in.question_id,
        team_id=answer_in.team_id,
        answer_text=answer_in.answer_text,
    )

    # Compute and broadcast updated leaderboard
    leaderboard_raw = crud.leaderboard_for_game(session, game_id=submission.question.round.game_id)
    standings = [
        schemas.LeaderboardEntry(
            team_id=team_id,
            team_name=data["team_name"],
            points=data["points"],
        )
        for team_id, data in leaderboard_raw
    ]
    await manager.broadcast(
        {
            "type": "leaderboard_update",
            "game_id": submission.question.round.game_id,
            "standings": jsonable_encoder(standings),
        }
    )

    return submission


# -- Leaderboard --


@app.get("/games/{game_id}/leaderboard", response_model=schemas.Leaderboard)
def get_leaderboard(game_id: int, session: Session = Depends(get_db_session)):
    leaderboard_raw = crud.leaderboard_for_game(session, game_id)
    standings = [
        schemas.LeaderboardEntry(
            team_id=team_id,
            team_name=data["team_name"],
            points=data["points"],
        )
        for team_id, data in leaderboard_raw
    ]
    return schemas.Leaderboard(game_id=game_id, standings=standings)


# -- WebSocket for live updates --


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo or process as needed
            await manager.broadcast({"message": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# -- Question broadcast --


@app.post("/questions/{question_id}/broadcast")
async def broadcast_question(question_id: int, request: Request, session: Session = Depends(get_db_session)):
    # Simple token check
    token = request.headers.get("X-Host-Token") if request else None
    if token != HOST_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    question = session.get(models.Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Prepare payload with essential info
    payload = {
        "type": "question",
        "game_id": question.round.game_id,
        "round_number": question.round.number,
        "question": {
            "id": question.id,
            "text": question.text,
            "media_url": question.media_url,
            "order": question.order,
        },
    }

    # Update game's current question pointer
    crud.set_current_question(session, question.round.game, question_id)

    await manager.broadcast(jsonable_encoder(payload))
    return {"status": "broadcasted"}


# Endpoint to get all questions for a game (for host UI)


@app.get("/games/{game_id}/questions", response_model=List[schemas.QuestionRead])
def list_game_questions(game_id: int, session: Session = Depends(get_db_session)):
    return crud.list_questions_for_game(session, game_id)


# Endpoint to get current question for a game (for late joiners)


@app.get("/games/{game_id}/current_question", response_model=schemas.CurrentQuestionResponse)
def get_current_question(game_id: int, session: Session = Depends(get_db_session)):
    game = crud.get_game(session, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.current_question_id:
        q = session.get(models.Question, game.current_question_id)
        return {"question": q}
    return {"question": None}


# -- Media upload --


@app.post("/media/upload")
async def upload_media(
    request: Request,
    file: UploadFile = File(...),
):
    token = request.headers.get("X-Host-Token")
    if token != HOST_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    filename = f"{int(datetime.utcnow().timestamp())}_{file.filename}"
    filepath = os.path.join(MEDIA_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(await file.read())

    return {"url": f"/media/{filename}"}


# -- Question update --


@app.put("/questions/{question_id}", response_model=schemas.QuestionRead)
def update_question(
    question_id: int,
    q_in: schemas.QuestionCreate,
    request: Request,
    session: Session = Depends(get_db_session),
):
    token = request.headers.get("X-Host-Token")
    if token != HOST_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    question = crud.update_question(
        session,
        question_id,
        text=q_in.text,
        answer=q_in.answer,
        media_url=q_in.media_url,
        order=q_in.order,
    )
    return question


# -- WiFi Access Point control --


@app.post("/wifi/start")
def wifi_start(request: Request):
    token = request.headers.get("X-Host-Token")
    if token != HOST_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    success = wifi.start_ap()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to start AP")
    return wifi.status_ap()


@app.post("/wifi/stop")
def wifi_stop(request: Request):
    token = request.headers.get("X-Host-Token")
    if token != HOST_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    success = wifi.stop_ap()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to stop AP")
    return wifi.status_ap()


@app.get("/wifi/status")
def wifi_status():
    return wifi.status_ap() 