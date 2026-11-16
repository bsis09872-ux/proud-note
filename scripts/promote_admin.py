"""관리자 승격 스크립트 (API 로는 관리자를 만들 수 없게 막아둠)

사용법 (프로젝트 루트에서):
    PYTHONPATH=src uv run python scripts/promote_admin.py proud@example.com
"""

import asyncio
import sys

from sqlalchemy import update

from shared.core.database import SessionLocal, close_db
from user.infrastructure.models import UserModel


async def promote(email: str) -> None:
    async with SessionLocal() as session:
        result = await session.execute(
            update(UserModel)
            .where(
                UserModel.email == email.strip().lower(), UserModel.resign.is_(False)
            )
            .values(role="ADMIN")
        )
        await session.commit()
    await close_db()
    if result.rowcount:
        print(f"✅ {email} -> ADMIN")
    else:
        print(f"❌ {email} 회원을 찾을 수 없어요 (탈퇴 회원 제외)")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    asyncio.run(promote(sys.argv[1]))
