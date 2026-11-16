import time
from typing import Any


class TTLCache:
    """프로세스 메모리 캐시 (워커 1개 기준).
    워커가 여러 개면 Redis 로 바꿔야 한다 -> 인터페이스(get/set/delete/clear)만 맞추면 됨.
    """

    def __init__(self, ttl_seconds: float, max_items: int = 1024):
        self.ttl = ttl_seconds
        self.max_items = max_items
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        item = self._store.get(key)
        if item is None:
            return None
        expires_at, value = item
        if expires_at < time.monotonic():
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        if len(self._store) >= self.max_items:
            self._evict()
        self._store[key] = (time.monotonic() + self.ttl, value)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    def _evict(self) -> None:
        now = time.monotonic()
        for k in [k for k, (exp, _) in self._store.items() if exp < now]:
            del self._store[k]
        if len(self._store) >= self.max_items:  # 그래도 꽉 차면 가장 오래된 것부터
            for k in list(self._store)[: self.max_items // 4]:
                del self._store[k]
