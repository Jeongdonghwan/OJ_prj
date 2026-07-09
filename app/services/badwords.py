"""금지어 필터 — 발견 시 관리자 검토 플래그(is_flagged)."""

BANNED_WORDS = [
    "리딩방", "수익보장", "수익 보장", "원금보장", "원금 보장",
    "고수익보장", "무료체험방", "매수신호", "투자자문 없이 고수익",
    "1:1 종목상담", "단톡방 입장",
]


def contains_banned_word(text):
    if not text:
        return False
    return any(w in text for w in BANNED_WORDS)
