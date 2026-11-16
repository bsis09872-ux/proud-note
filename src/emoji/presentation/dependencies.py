from emoji.application.service import EmojiService


def provide_emoji_service() -> EmojiService:
    raise NotImplementedError("EmojiService 의존성이 주입되지 않았습니다.")
