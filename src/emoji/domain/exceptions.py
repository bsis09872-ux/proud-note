from shared.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)


class EmojiNotFound(
    NotFoundException, code="EMOJI_NOT_FOUND", message="그런 이모지는 없어요 🫥"
): ...


class EmojiNameTaken(
    ConflictException, code="EMOJI_NAME_TAKEN", message="이미 있는 이모지 이름이에요 🙈"
): ...


class InvalidEmoji(
    ValidationException, code="INVALID_EMOJI", message="이모지를 확인해 주세요 🧐"
): ...


class InvalidEmojiImage(
    ValidationException,
    code="INVALID_EMOJI_IMAGE",
    message="PNG·GIF·JPG·WEBP 이미지 256KB 이하만 올릴 수 있어요 🖼️",
): ...


class NotEmojiOwner(
    ForbiddenException,
    code="NOT_EMOJI_OWNER",
    message="내가 등록한 이모지만 지울 수 있어요 🙅",
): ...


class ReactionAlreadyExists(
    ConflictException,
    code="REACTION_ALREADY_EXISTS",
    message="이미 이 이모지로 반응했어요 😊",
): ...


class ReactionNotFound(
    NotFoundException, code="REACTION_NOT_FOUND", message="취소할 반응이 없어요 🤔"
): ...
