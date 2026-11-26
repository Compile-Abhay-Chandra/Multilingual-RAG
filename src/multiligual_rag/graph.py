"""LangGraph workflow for retrieve -> assess evidence -> answer or abstain."""

from __future__ import annotations

import os
from typing import TypedDict

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from multiligual_rag.retrieval import Hit, PassageIndex, RetrievalMethod

load_dotenv()

ABSTENTION = "Insufficient information is available in the uploaded documents to answer this question."
DEFAULT_THRESHOLDS = {"lexical": 0.10, "dense": 0.34, "hybrid": 0.34}


class QAState(TypedDict, total=False):
    question: str
    method: RetrievalMethod
    top_k: int
    hits: list[Hit]
    answerable: bool
    answer: str
    model: str


def build_graph(index: PassageIndex, thresholds: dict[str, float] | None = None):
    evidence_thresholds = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    def retrieve(state: QAState) -> QAState:
        hits = index.search(state["question"], state.get("method", "hybrid"), state.get("top_k", 5))
        return {"hits": hits}

    def assess(state: QAState) -> QAState:
        hits = state.get("hits", [])
        method = state.get("method", "hybrid")
        # Thresholds are starter defaults. Calibrate against a labeled validation set.
        threshold = evidence_thresholds[method]
        answerable = bool(hits and hits[0].evidence_score >= threshold)
        return {"answerable": answerable, "answer": "" if answerable else ABSTENTION}

    def generate(state: QAState) -> QAState:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not configured. Add it to your .env file.")
        model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        context = "\n\n".join(
            f"[{hit.passage.id}] Document: {hit.passage.document_name}; page: {hit.passage.page or 'unknown'}\n{hit.passage.text}"
            for hit in state.get("hits", [])
        )
        llm = ChatGroq(model=model_name, temperature=0, api_key=api_key)
        response = llm.invoke([
            SystemMessage(content=(
                "You support English, Hindi, and Hinglish questions and answers only. If a question is in another language, "
                "briefly say that only English, Hindi, and Hinglish are supported. For supported questions, use only the "
                "supplied document excerpts. If the excerpts do not support an answer, "
                "say that the documents do not contain enough information. Cite supporting passage IDs in square brackets, "
                "for example [doc1-p2-c3]. Do not invent facts or citations. Reply in English, Hindi, or Hinglish to match the question."
            )),
            HumanMessage(content=f"Question:\n{state['question']}\n\nDocument excerpts:\n{context}"),
        ])
        return {"answer": str(response.content), "model": model_name}

    def route(state: QAState) -> str:
        return "generate" if state.get("answerable") else "abstain"

    workflow = StateGraph(QAState)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("assess", assess)
    workflow.add_node("generate", generate)
    workflow.add_node("abstain", lambda state: {})
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "assess")
    workflow.add_conditional_edges("assess", route, {"generate": "generate", "abstain": "abstain"})
    workflow.add_edge("generate", END)
    workflow.add_edge("abstain", END)
    return workflow.compile()

