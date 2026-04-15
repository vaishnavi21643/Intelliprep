import shutil
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ragbase.chain import ask_question, create_chain
from ragbase.config import Config
from ragbase.ingestor import Ingestor
from ragbase.model import create_llm
from ragbase.retriever import create_retriever
from ragbase.uploader import upload_files

load_dotenv()

_chains: dict[str, object] = {}


def _cleanup_all():
    """Delete all per-session DB folders and tmp docs."""
    shutil.rmtree(Config.Path.DATABASE_DIR, ignore_errors=True)
    shutil.rmtree(Config.Path.DOCUMENTS_DIR, ignore_errors=True)
    # Also clean any session-specific db folders
    app_home = Config.Path.APP_HOME
    for folder in app_home.glob("docs-db-*"):
        shutil.rmtree(folder, ignore_errors=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _cleanup_all()
    yield
    _cleanup_all()
    _chains.clear()


app = FastAPI(title="RagBase API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    session_id: str
    question: str


class UploadResponse(BaseModel):
    session_id: str
    message: str
    files: list[str]


class Source(BaseModel):
    content: str


class AnswerResponse(BaseModel):
    answer: str
    sources: list[Source]


def _build_chain(file_paths: list[Path], db_path: Path):
    """Build RAG chain using a session-specific DB path to avoid Qdrant lock."""
    vector_store = Ingestor(db_path=db_path).ingest(file_paths)
    llm = create_llm()
    retriever = create_retriever(llm, vector_store=vector_store)
    return create_chain(llm, retriever)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/upload", response_model=UploadResponse)
async def upload(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    session_id = str(uuid.uuid4())

    # Each session gets its own isolated DB folder — no lock conflicts
    db_path = Config.Path.APP_HOME / f"docs-db-{session_id}"

    saved_paths = await upload_files(files)

    try:
        chain = _build_chain(saved_paths, db_path)
    except Exception as exc:
        shutil.rmtree(db_path, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Failed to build chain: {exc}")

    _chains[session_id] = chain
    return UploadResponse(
        session_id=session_id,
        message=f"Ingested {len(saved_paths)} file(s) successfully.",
        files=[p.name for p in saved_paths],
    )


@app.post("/ask", response_model=AnswerResponse)
async def ask(body: QuestionRequest):
    chain = _chains.get(body.session_id)
    if chain is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Please upload documents first.",
        )

    full_response = ""
    sources: list[Source] = []

    async for event in ask_question(chain, body.question, session_id=body.session_id):
        if isinstance(event, str):
            full_response += event
        elif isinstance(event, list):
            sources.extend(Source(content=doc.page_content) for doc in event)

    return AnswerResponse(answer=full_response, sources=sources)


@app.post("/ask/stream")
async def ask_stream(body: QuestionRequest):
    chain = _chains.get(body.session_id)
    if chain is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Please upload documents first.",
        )

    async def event_generator() -> AsyncGenerator[str, None]:
        import json
        async for event in ask_question(chain, body.question, session_id=body.session_id):
            if isinstance(event, str):
                payload = json.dumps({"type": "token", "value": event})
                yield f"data: {payload}\n\n"
            elif isinstance(event, list):
                for doc in event:
                    payload = json.dumps({"type": "source", "value": doc.page_content})
                    yield f"data: {payload}\n\n"
        yield 'data: {"type": "done"}\n\n'

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    if session_id not in _chains:
        raise HTTPException(status_code=404, detail="Session not found.")
    del _chains[session_id]
    # Clean up that session's DB folder
    db_path = Config.Path.APP_HOME / f"docs-db-{session_id}"
    shutil.rmtree(db_path, ignore_errors=True)
    return {"message": "Session deleted."}