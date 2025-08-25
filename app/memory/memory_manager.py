from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, DefaultDict, Dict, List, Optional
import hashlib


class MemoryManager:
    """Utility class to manage conversation memory with deduplication and events."""

    def __init__(self, conversation_service):
        self.conversation_service = conversation_service
        self._subscribers: DefaultDict[str, List[Callable[[Dict[str, Any]], None]]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Event system
    # ------------------------------------------------------------------
    def subscribe(self, event_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Register a handler for a specific event type."""
        self._subscribers[event_type].append(handler)

    def _emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        for handler in self._subscribers.get(event_type, []):
            handler(payload)

    # ------------------------------------------------------------------
    # Message helpers
    # ------------------------------------------------------------------
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Add a message with simple deduplication and optional event emission."""
        last = self.conversation_service.get_last_message(conversation_id)
        if last:
            last_hash = hashlib.sha256((last.role + last.content).encode()).hexdigest()
            new_hash = hashlib.sha256((role + content).encode()).hexdigest()
            if last_hash == new_hash:
                return last

        message = self.conversation_service.add_message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata=metadata,
        )

        event_type = metadata.get("event_type") if metadata else None
        if event_type:
            self._emit(
                event_type,
                {
                    "conversation_id": conversation_id,
                    "role": role,
                    "content": content,
                    "metadata": metadata,
                },
            )
        return message

    def get_recent_history(self, conversation_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetch recent conversation history."""
        return self.conversation_service.get_conversation_history(conversation_id, limit)

    @staticmethod
    def build_prompt(message: str, conversation_history: List[Dict[str, Any]]) -> str:
        """Combine message with recent history to create a prompt."""
        if not conversation_history:
            return message

        history_text = ""
        for msg in conversation_history[-5:]:
            role = "Người dùng" if msg["role"] == "user" else "Trợ lý"
            history_text += f"{role}: {msg['content']}\n"

        return f"Lịch sử hội thoại gần đây:\n{history_text}\nNgười dùng hiện tại: {message}"
