"""글쓰기 화면 상단에 보여줄 귀여운 가이드"""

from space.domain.space import FRIENDS, PLAZA

FIELDS = [
    {
        "key": "learned",
        "label": "📚 오늘 알게 된 것",
        "hint": "새로 배운 개념, 알게 된 단축키, 사소한 깨달음까지 다 좋아요!",
        "example": "git rebase -i 로 커밋을 합칠 수 있다는 걸 알았다",
    },
    {
        "key": "achieved",
        "label": "🏆 오늘 해낸 것",
        "hint": "끝낸 일, 고친 버그, 미루던 일 시작하기도 대단한 거예요",
        "example": "3일 묵은 CORS 에러 드디어 해결!",
    },
    {
        "key": "proud_of_me",
        "label": "🌷 오늘의 나",
        "hint": "오늘의 나에게 건네는 칭찬 한마디",
        "example": "오늘 잘 웃었다! 물도 8잔 마셨다 💧",
    },
]

COMMON_TIPS = [
    "세 칸 중 하나만 채워도 충분해요 🙆",
    "거창하지 않아도 괜찮아요. 작은 반짝임이 모이면 별이 돼요 ✨",
    "#태그 를 달면 나중에 모아보기 쉬워요 (최대 5개)",
]

SPACE_TIPS = {
    FRIENDS: [
        "🏡 친구 공간은 닉네임으로 보여요",
        "칭찬 댓글과 이모지로 서로 응원해 줘요 💌",
    ],
    PLAZA: [
        "🌏 광장에서는 모두 '익명의 프라우더'예요",
        "하루에 한 번만 올릴 수 있어요. 오늘의 베스트를 골라봐요 🌙",
        "최신 50개만 머물고, 오래된 글은 별똥별처럼 사라져요 🌠",
        "비회원은 수정·삭제용 비밀번호를 꼭 기억해 주세요 🔑",
    ],
}


def writing_guide(space_id: str | None) -> dict:
    return {
        "title": "오늘의 프라우드 노트 ✍️",
        "greeting": "오늘도 수고했어요! 어떤 하루였는지 들려줄래요? 🐣",
        "fields": FIELDS,
        "tips": COMMON_TIPS + SPACE_TIPS.get(space_id or "", []),
    }
