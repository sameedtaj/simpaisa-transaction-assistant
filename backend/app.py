
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from backend.openai_agent import ask_database

app = FastAPI(
    title="MCP Database Chatbot API",
    description="FastAPI wrapper for GPT + MCP + PostgreSQL read-only chatbot",
    version="1.0.0"
)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    success: bool
    question: str
    sql: str | None = None
    result: str | dict | list | None = None
    error: str | None = None


@app.get("/")
def home():
    return {
        "status": "running",
        "message": "MCP Database Chatbot API is live"
    }


@app.get("/health")
def health_check():
    return {
        "success": True,
        "service": "FastAPI",
        "agent": "ready",
        "mcp": "configured"
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response = await ask_database(request.question)

        return ChatResponse(
            success=response.get("success", False),
            question=request.question,
            sql=response.get("sql"),
            result=response.get("result") or response.get("answer"),
            error=response.get("error")
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )
