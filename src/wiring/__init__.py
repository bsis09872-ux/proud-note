from fastapi import FastAPI

from wiring.auth import wire_auth_dependencies
from wiring.emoji import wire_emoji_dependencies
from wiring.note import wire_note_dependencies
from wiring.space import wire_space_dependencies
from wiring.user import wire_user_dependencies


def wire_dependencies(app: FastAPI) -> None:
    """presentation 의 플레이스홀더 -> 실제 구현 (FastAPI dependency_overrides)"""
    wire_user_dependencies(app)
    wire_auth_dependencies(app)
    wire_space_dependencies(app)
    wire_note_dependencies(app)
    wire_emoji_dependencies(app)
