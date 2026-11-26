"""FastAPI application for IndicRAG-QA."""

from __future__ import annotations

import re
import hashlib
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from multiligual_rag.corpus import extract_bytes
from multiligual_rag.graph import build_graph
from multiligual_rag.retrieval import PassageIndex

load_dotenv()

index = PassageIndex()
documents: dict[str, dict] = {}
qa_graph = build_graph(index)


class QuestionRequest(BaseModel):
    question: str = Field(min_length=2, max_length=4000)
    retrieval_method: Literal["lexical", "dense", "hybrid"] = "hybrid"
    top_k: int = Field(default=5, ge=1, le=20)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(
    title="IndicRAG-QA API",
    description="Evidence-grounded multilingual document question answering with lexical, dense, and hybrid retrieval.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "ok", "document_count": len(documents), "passage_count": len(index.passages)}


@app.get("/documents")
def list_documents():
    return {"documents": list(documents.values())}


@app.post("/documents")
async def upload_document(file: UploadFile = File(...)):
    filename = file.filename or "uploaded-document"
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if suffix not in {"pdf", "txt", "md"}:
        raise HTTPException(status_code=415, detail="Upload a PDF, TXT, or Markdown file.")
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(raw) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="The maximum upload size is 20 MB.")
    try:
        new_passages = extract_bytes(filename, raw)
        doc_id = hashlib.sha1(filename.encode("utf-8") + raw).hexdigest()[:12]
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read document: {exc}") from exc
    if not new_passages:
        raise HTTPException(status_code=400, detail="No extractable text was found in this file.")
    index.add(new_passages)
    metadata = {"document_id": doc_id, "filename": filename, "passage_count": len(new_passages), "pages": len({p.page for p in new_passages if p.page})}
    documents[doc_id] = metadata
    return metadata


@app.delete("/documents/{document_id}")
def delete_document(document_id: str):
    if document_id not in documents:
        raise HTTPException(status_code=404, detail="Document not found.")
    index.remove_document(document_id)
    return {"deleted": documents.pop(document_id)}


@app.post("/ask")
def ask(request: QuestionRequest):
    if not index.passages:
        raise HTTPException(status_code=400, detail="Upload at least one document before asking a question.")
    try:
        result = qa_graph.invoke({
            "question": request.question,
            "method": request.retrieval_method,
            "top_k": request.top_k,
        })
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Question answering failed: {exc}") from exc
    hits = result.get("hits", [])
    question = request.question
    if re.search(r"[\u0900-\u097f]", question):
        query_type = "hindi"
    elif re.search(r"\b(ke liye|kya|hai|kaise|kab|kitna|kitni|hoga|chahiye|ka|ki|ko|mein|nahi)\b", question, re.IGNORECASE):
        query_type = "hinglish-likely"
    else:
        query_type = "english-likely"
    return {
        "question": request.question,
        "retrieval_method": request.retrieval_method,
        "answerability": "ANSWERABLE" if result.get("answerable") else "UNANSWERABLE",
        "answer": result.get("answer", ""),
        "evidence_score": round(hits[0].evidence_score, 4) if hits else 0.0,
        "score_note": "Retrieval score used as an uncalibrated evidence-sufficiency heuristic; calibrate on labeled validation data.",
        "model": result.get("model"),
        "query_type": query_type,
        "sources": [
            {
                "passage_id": h.passage.id,
                "document_id": h.passage.document_id,
                "document_name": h.passage.document_name,
                "page": h.passage.page,
                "score": round(h.score, 4),
                "evidence_score": round(h.evidence_score, 4),
                "text": h.passage.text,
            }
            for h in hits
        ],
    }


def run() -> None:
    import uvicorn

    uvicorn.run("multiligual_rag.api:app", host="0.0.0.0", port=8000, reload=False)

