import os
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .db import Base, SessionLocal, engine
from .schemas import Board, Card, CardCreate, CardMove, CardUpdate, ColumnInfo
from .store import COLUMNS, CardStore
from .telemetry import setup_telemetry

# Paths that are infrastructure, not part of the user journey: they are
# polled every few seconds by Docker/Kubernetes and would drown the metrics.
UNMETERED_PATHS = {"/healthz", "/readyz"}


def create_schema(retries: int = 30, delay_s: float = 1.0) -> None:
    # In Compose/Kubernetes the API can start before Postgres accepts
    # connections; retry instead of crash-looping.
    for attempt in range(retries):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(delay_s)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_schema()
    yield


app = FastAPI(title="Boardly API", lifespan=lifespan)
requests_counter, duration_histogram, logger = setup_telemetry(app, engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def record_request(request: Request, call_next):
    if request.url.path in UNMETERED_PATHS:
        return await call_next(request)
    started = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        route = request.scope.get("route")
        route_path = route.path if route else "unmatched"
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        attributes = {
            "http.route": route_path,
            "http.method": request.method,
            "http.status_code": status_code,
        }
        requests_counter.add(1, attributes)
        duration_histogram.record(
            duration_ms, {"http.route": route_path, "http.method": request.method}
        )
        extra = {**attributes, "duration_ms": duration_ms}
        card_id = request.scope.get("path_params", {}).get("card_id")
        if card_id:
            extra["card_id"] = card_id
        log = logger.error if status_code >= 500 else logger.info
        log("board api request", extra=extra)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_store(db: Session = Depends(get_db)) -> CardStore:
    return CardStore(db)


@app.get("/healthz")
def health():
    return {"status": "ok"}


@app.get("/readyz")
def ready(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="database unavailable")
    return {"status": "ok"}


@app.get("/board", response_model=Board)
def get_board(store: CardStore = Depends(get_store)):
    return Board(
        columns=[ColumnInfo(**c) for c in COLUMNS],
        cards=[Card(**c) for c in store.list_cards()],
    )


@app.post("/cards", response_model=Card, status_code=status.HTTP_201_CREATED)
def create_card(payload: CardCreate, store: CardStore = Depends(get_store)):
    card = store.create(
        title=payload.title, description=payload.description, column=payload.column
    )
    return Card(**card)


@app.patch("/cards/{card_id}", response_model=Card)
def update_card(
    card_id: str, payload: CardUpdate, store: CardStore = Depends(get_store)
):
    card = store.update(card_id, title=payload.title, description=payload.description)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return Card(**card)


@app.patch("/cards/{card_id}/move", response_model=Card)
def move_card(card_id: str, payload: CardMove, store: CardStore = Depends(get_store)):
    card = store.update(card_id, column=payload.column)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return Card(**card)


@app.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(card_id: str, store: CardStore = Depends(get_store)):
    if not store.delete(card_id):
        raise HTTPException(status_code=404, detail="Card not found")
