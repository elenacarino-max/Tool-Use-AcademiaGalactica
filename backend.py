"""Loopback-only educational FastAPI backend. NOT a production auth service."""
from __future__ import annotations
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from tool_engine import ToolEngine, CATALOG

ROOT = Path(__file__).parent
app = FastAPI(title='Academia Galactica - backend local de entrenamiento', version='3.0.0')

@dataclass
class Session:
    csrf: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    role: str = 'operadora'  # Assigned by this training server, NEVER by a model argument.
    expires: float = field(default_factory=lambda: time.monotonic() + 7200)
    engine: ToolEngine = field(default_factory=ToolEngine)

SESSIONS: dict[str, Session] = {}

class ToolRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    call_id: str = Field(default_factory=lambda: f'call_{uuid4().hex}', min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=80)
    arguments: Any
    approval_token: str | None = Field(default=None, max_length=128)

@app.middleware('http')
async def local_only(request: Request, call_next):
    if request.url.hostname not in {'127.0.0.1', 'localhost', '::1'}:
        return JSONResponse({'detail': 'Solo se admiten nombres de host loopback.'}, status_code=403)
    origin = request.headers.get('origin')
    expected = f'{request.url.scheme}://{request.headers.get("host", "")}'
    if origin and origin != expected:
        return JSONResponse({'detail': 'Origen no permitido; usa el frontend del mismo servidor.'}, status_code=403)
    content_length = request.headers.get('content-length')
    try:
        if content_length and int(content_length) > 32768:
            return JSONResponse({'detail': 'Peticion demasiado grande.'}, status_code=413)
    except ValueError:
        return JSONResponse({'detail': 'Content-Length invalido.'}, status_code=400)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Cache-Control'] = 'no-store'
    return response

@app.get('/')
def index():
    return FileResponse(ROOT / 'index.html', media_type='text/html')

@app.get('/api/health')
def health():
    return {'protocol': 'galactica-v3', 'runtime': 'python-local', 'llm_connected': False,
            'mode': 'single-user local training; fictional data'}

@app.post('/api/session')
def session_start(response: Response):
    now = time.monotonic()
    for key in list(SESSIONS):
        if SESSIONS[key].expires <= now:
            del SESSIONS[key]
    if len(SESSIONS) >= 100:
        raise HTTPException(429, 'Demasiadas sesiones de entrenamiento.')
    sid = secrets.token_urlsafe(32)
    session = Session()
    SESSIONS[sid] = session
    response.set_cookie('galactica_session', sid, httponly=True, samesite='strict', max_age=7200, path='/')
    return {'csrf': session.csrf, 'role': session.role, 'demo_only': True}

def current_session(request: Request) -> Session:
    sid = request.cookies.get('galactica_session', '')
    session = SESSIONS.get(sid)
    if not session or session.expires <= time.monotonic():
        raise HTTPException(401, 'Abre una sesion de entrenamiento primero.')
    csrf = request.headers.get('x-csrf-token', '')
    if not secrets.compare_digest(csrf, session.csrf):
        raise HTTPException(403, 'Token CSRF ausente o incorrecto.')
    return session

@app.get('/api/tools')
def tools():
    return {'tools': list(CATALOG.values())}

@app.post('/api/approve')
def approve(body: ToolRequest, session: Session = Depends(current_session)):
    return session.engine.approve(body.name, body.arguments, session.role)

@app.post('/api/execute')
def execute(body: ToolRequest, session: Session = Depends(current_session)):
    return session.engine.execute(body.name, body.arguments, role=session.role,
                                  call_id=body.call_id, approval_token=body.approval_token)
