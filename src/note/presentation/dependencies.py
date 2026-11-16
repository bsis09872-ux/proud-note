from fastapi import Request

from note.application.service import CommentService, NoteService
from note.infrastructure.security import hash_client_ip


def provide_note_service() -> NoteService:
    raise NotImplementedError("NoteService 의존성이 주입되지 않았습니다.")


def provide_comment_service() -> CommentService:
    raise NotImplementedError("CommentService 의존성이 주입되지 않았습니다.")


def get_client_ip_hash(request: Request) -> str:
    """비회원 식별용 IP 해시 (배포 시 uvicorn --proxy-headers 필요)"""
    ip = request.client.host if request.client else "unknown"
    return hash_client_ip(ip)
