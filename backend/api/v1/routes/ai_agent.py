"""
AI Agent API Routes
DeepSeek-powered chat assistant with REST and WebSocket endpoints.

REST:  POST /ai/query       – single prompt → response
       POST /ai/analyze-project – project structure analysis
WS:    /ws/agent/{token}    – streaming chat with conversation context

Conversation history is stored in the MultiLevelCache (Redis → in-memory)
keyed by user_id, with a configurable TTL.
"""
import json
import logging
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from core.config import get_settings
from core.response import success_response, error_response
from core.security import get_supabase_user, verify_supabase_jwt

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/ai", tags=["AI Agent"])

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEEPSEEK_TIMEOUT = 90.0           # seconds – streaming can be slow
MAX_CONVERSATION_TURNS = 20       # keep last N user+assistant pairs
CONVERSATION_TTL = 1800           # 30 min cache TTL
MAX_TOKENS_DEFAULT = 2048
MAX_TOKENS_CEILING = 4096

CREDIT_ASSISTANT_PROMPT = """\
You are Credit Clarity AI, a helpful assistant specializing in credit repair,
FCRA dispute strategy, credit report analysis, and financial literacy.

Rules:
- Give clear, actionable advice grounded in FCRA / FDCPA regulations.
- When discussing dispute strategies, mention the relevant FCRA section.
- Never provide legal advice; recommend consulting a licensed attorney for
  legal questions.
- Be concise. Use markdown formatting for readability.
- If the user shares tradeline data, analyse it and suggest next steps.
"""

PROJECT_ANALYSIS_PROMPT = """\
You are an AI code assistant. Analyze this project structure and create a
clear, markdown-based directory map that explains each folder and file's
purpose for other AI agents. Include these details:

- Backend: API routes, services, workers, schemas, middleware, utils, tests.
- Frontend: Pages, components, hooks, services, integrations, utils, types.
- Database: Supabase migrations, edge functions, config.
- Documentation: PRDs, architecture, API, security docs.
- Workflows: session artifacts, active tasks, summaries, process packages.
- AI agent usage: Mark AI-specific folders/files.
- Debugging: logs, error handlers, test files.
- Important relationships (services → frontend components/pages).

Output a single structured markdown file using headers and bullet points.
"""

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class AgentQueryRequest(BaseModel):
    """Body for POST /ai/query."""
    message: str = Field(..., min_length=1, max_length=4000)
    context: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Extra context (current page, user data summary, etc.)",
    )
    max_tokens: int = Field(default=MAX_TOKENS_DEFAULT, ge=100, le=MAX_TOKENS_CEILING)
    conversation_id: Optional[str] = Field(
        default=None,
        description="Resume a previous conversation (defaults to user's latest)",
    )


class AnalyzeProjectRequest(BaseModel):
    """Body for POST /ai/analyze-project."""
    context: str = Field(default="", max_length=4000)
    max_tokens: int = Field(default=2500, ge=100, le=MAX_TOKENS_CEILING)


# ---------------------------------------------------------------------------
# Conversation store (backed by MultiLevelCache)
# ---------------------------------------------------------------------------

def _conv_cache_key(user_id: str, conv_id: Optional[str] = None) -> str:
    suffix = conv_id or "default"
    return f"ai_conv:{user_id}:{suffix}"


async def _get_conversation(user_id: str, conv_id: Optional[str] = None) -> List[Dict[str, str]]:
    from services.cache_service import cache
    key = _conv_cache_key(user_id, conv_id)
    history = await cache.get(key)
    return history if isinstance(history, list) else []


async def _save_conversation(
    user_id: str,
    history: List[Dict[str, str]],
    conv_id: Optional[str] = None,
) -> None:
    from services.cache_service import cache
    # Trim to last N turns (each turn = user + assistant = 2 messages)
    trimmed = history[-(MAX_CONVERSATION_TURNS * 2):]
    key = _conv_cache_key(user_id, conv_id)
    await cache.set(key, trimmed, ttl=CONVERSATION_TTL)


# ---------------------------------------------------------------------------
# DeepSeek helpers
# ---------------------------------------------------------------------------

async def _call_deepseek(
    messages: List[Dict[str, str]],
    max_tokens: int = MAX_TOKENS_DEFAULT,
    temperature: float = 0.3,
) -> str:
    """Non-streaming chat completion."""
    if not settings.deepseek_api_key:
        raise HTTPException(status_code=503, detail="DeepSeek API key not configured")

    payload = {
        "model": settings.deepseek_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=DEEPSEEK_TIMEOUT) as client:
        try:
            resp = await client.post(
                f"{settings.deepseek_api_base}/chat/completions",
                json=payload,
                headers=headers,
            )
        except httpx.TimeoutException:
            logger.error("DeepSeek API timed out")
            raise HTTPException(status_code=504, detail="AI service timed out")
        except httpx.RequestError as exc:
            logger.error("DeepSeek request error: %s", exc)
            raise HTTPException(status_code=502, detail="AI service unavailable")

    if resp.status_code != 200:
        logger.error("DeepSeek %d: %s", resp.status_code, resp.text[:300])
        raise HTTPException(status_code=502, detail="AI service returned an error")

    choices = resp.json().get("choices", [])
    if not choices:
        raise HTTPException(status_code=502, detail="AI service returned empty response")
    return choices[0]["message"]["content"]


async def _stream_deepseek(
    messages: List[Dict[str, str]],
    max_tokens: int = MAX_TOKENS_DEFAULT,
    temperature: float = 0.3,
):
    """Async generator that yields content deltas from DeepSeek SSE stream."""
    if not settings.deepseek_api_key:
        yield json.dumps({"type": "error", "content": "DeepSeek API key not configured"})
        return

    payload = {
        "model": settings.deepseek_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }
    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=DEEPSEEK_TIMEOUT) as client:
        try:
            async with client.stream(
                "POST",
                f"{settings.deepseek_api_base}/chat/completions",
                json=payload,
                headers=headers,
            ) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    logger.error("DeepSeek stream %d: %s", resp.status_code, body[:300])
                    yield json.dumps({"type": "error", "content": "AI service error"})
                    return

                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

        except httpx.TimeoutException:
            yield json.dumps({"type": "error", "content": "AI service timed out"})
        except httpx.RequestError as exc:
            logger.error("DeepSeek stream error: %s", exc)
            yield json.dumps({"type": "error", "content": "AI service unavailable"})


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------

@router.post("/query")
async def agent_query(
    body: AgentQueryRequest,
    user: dict = Depends(get_supabase_user),
):
    """Send a prompt to DeepSeek and return the response.

    Maintains per-user conversation context via cache.
    """
    user_id = user["id"]

    # Build message list with history
    history = await _get_conversation(user_id, body.conversation_id)
    messages: List[Dict[str, str]] = [{"role": "system", "content": CREDIT_ASSISTANT_PROMPT}]

    # Inject optional page/data context
    if body.context:
        messages.append({"role": "system", "content": f"Current context:\n{body.context}"})

    messages.extend(history)
    messages.append({"role": "user", "content": body.message})

    # Call DeepSeek
    answer = await _call_deepseek(messages, max_tokens=body.max_tokens)

    # Persist conversation
    history.append({"role": "user", "content": body.message})
    history.append({"role": "assistant", "content": answer})
    await _save_conversation(user_id, history, body.conversation_id)

    return success_response(data={
        "message": answer,
        "conversation_id": body.conversation_id or "default",
        "model": settings.deepseek_model,
        "timestamp": datetime.utcnow().isoformat(),
    })


@router.post("/analyze-project")
async def analyze_project(
    body: AnalyzeProjectRequest,
    user: dict = Depends(get_supabase_user),
):
    """Send project info to DeepSeek and return a markdown directory map."""
    messages = [
        {"role": "system", "content": PROJECT_ANALYSIS_PROMPT},
        {"role": "user", "content": body.context or "Analyze the Credit Clarity project structure."},
    ]
    content = await _call_deepseek(messages, max_tokens=body.max_tokens, temperature=0.1)

    return success_response(data={
        "markdown": content,
        "model": settings.deepseek_model,
    })


# ---------------------------------------------------------------------------
# WebSocket endpoint — streaming chat
# ---------------------------------------------------------------------------

@router.websocket("/stream/{token}")
async def agent_ws_stream(websocket: WebSocket, token: str):
    """WebSocket endpoint for streaming AI responses.

    Authentication is done via the URL token parameter because browsers
    cannot send Authorization headers on WebSocket upgrade requests.

    Protocol:
        Client sends JSON:
            {"message": "...", "context": "...", "max_tokens": 2048}

        Server sends JSON frames:
            {"type": "token",  "content": "partial text..."}
            {"type": "done",   "content": "full response", "timestamp": "..."}
            {"type": "error",  "content": "error message"}
    """
    # Authenticate via token in URL
    try:
        user = verify_supabase_jwt(token)
    except Exception:
        await websocket.close(code=4001, reason="Invalid authentication token")
        return

    user_id = user["id"]
    await websocket.accept()
    logger.info("AI WebSocket connected for user %s", user_id)

    try:
        while True:
            raw = await websocket.receive_text()

            # Parse client message
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "content": "Invalid JSON"})
                continue

            msg_type = data.get("type", "message")

            # Ping/pong keepalive
            if msg_type == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
                continue

            # Clear conversation
            if msg_type == "clear":
                from services.cache_service import cache
                await cache.delete(_conv_cache_key(user_id, data.get("conversation_id")))
                await websocket.send_json({"type": "cleared"})
                continue

            user_message = data.get("message", "").strip()
            if not user_message:
                await websocket.send_json({"type": "error", "content": "Empty message"})
                continue

            if len(user_message) > 4000:
                await websocket.send_json({"type": "error", "content": "Message too long (max 4000 chars)"})
                continue

            conv_id = data.get("conversation_id")
            context = data.get("context")
            max_tokens = min(data.get("max_tokens", MAX_TOKENS_DEFAULT), MAX_TOKENS_CEILING)

            # Build messages
            history = await _get_conversation(user_id, conv_id)
            messages: List[Dict[str, str]] = [
                {"role": "system", "content": CREDIT_ASSISTANT_PROMPT},
            ]
            if context:
                messages.append({"role": "system", "content": f"Current context:\n{context}"})
            messages.extend(history)
            messages.append({"role": "user", "content": user_message})

            # Stream response
            full_response = ""
            async for chunk in _stream_deepseek(messages, max_tokens=max_tokens):
                # Check if chunk is an error JSON
                if chunk.startswith("{"):
                    try:
                        err = json.loads(chunk)
                        if err.get("type") == "error":
                            await websocket.send_json(err)
                            break
                    except json.JSONDecodeError:
                        pass

                full_response += chunk
                await websocket.send_json({"type": "token", "content": chunk})

            if full_response:
                # Send done frame
                await websocket.send_json({
                    "type": "done",
                    "content": full_response,
                    "timestamp": datetime.utcnow().isoformat(),
                })

                # Persist conversation
                history.append({"role": "user", "content": user_message})
                history.append({"role": "assistant", "content": full_response})
                await _save_conversation(user_id, history, conv_id)

    except WebSocketDisconnect:
        logger.info("AI WebSocket disconnected for user %s", user_id)
    except Exception as exc:
        logger.error("AI WebSocket error for user %s: %s", user_id, exc)
        try:
            await websocket.send_json({"type": "error", "content": "Internal error"})
        except Exception:
            pass
