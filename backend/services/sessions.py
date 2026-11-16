"""In-memory conversation sessions with TTL expiry and bounded history."""
from __future__ import annotations

import threading
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


@dataclass
class _Session:
    messages: list[BaseMessage] = field(default_factory=list)
    touched: float = field(default_factory=time.monotonic)


class SessionStore:
    """Swap this class for a Redis-backed one to scale beyond a single process."""

    def __init__(self, ttl_minutes: int, max_sessions: int, max_turns: int) -> None:
        self._ttl = ttl_minutes * 60
        self._max_sessions = max_sessions
        self._max_messages = max_turns * 2
        self._sessions: OrderedDict[str, _Session] = OrderedDict()
        self._lock = threading.RLock()

    def _purge(self) -> None:
        now = time.monotonic()
        for sid in [s for s, v in self._sessions.items() if now - v.touched > self._ttl]:
            del self._sessions[sid]
        while len(self._sessions) > self._max_sessions:
            self._sessions.popitem(last=False)  # evict least recently used

    def create(self) -> str:
        with self._lock:
            self._purge()
            sid = uuid.uuid4().hex
            self._sessions[sid] = _Session()
            return sid

    def get_history(self, session_id: str) -> list[BaseMessage]:
        with self._lock:
            self._purge()
            session = self._sessions.get(session_id)
            return list(session.messages) if session else []

    def append_turn(self, session_id: str, question: str, answer: str) -> None:
        with self._lock:
            session = self._sessions.setdefault(session_id, _Session())
            session.messages += [HumanMessage(question), AIMessage(answer)]
            session.messages = session.messages[-self._max_messages :]
            session.touched = time.monotonic()
            self._sessions.move_to_end(session_id)

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)
