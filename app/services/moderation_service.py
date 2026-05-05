from collections import defaultdict
from datetime import datetime, timedelta

from app.core.constants import INVITE_PATTERN, URL_PATTERN


class FloodTracker:
    def __init__(self, flood_limit: int, flood_window_secs: int) -> None:
        self._flood_limit = flood_limit
        self._flood_window_secs = flood_window_secs
        self._tracker: dict[int, dict[int, list[datetime]]] = defaultdict(lambda: defaultdict(list))

    def hit(self, chat_id: int, user_id: int) -> bool:
        now = datetime.utcnow()
        threshold = now - timedelta(seconds=self._flood_window_secs)

        times = self._tracker[chat_id][user_id]
        self._tracker[chat_id][user_id] = [stamp for stamp in times if stamp > threshold]
        self._tracker[chat_id][user_id].append(now)
        return len(self._tracker[chat_id][user_id]) > self._flood_limit


def contains_bad_words(text: str, bad_words: set[str]) -> bool:
    words = text.lower().split()
    normalized = {word.strip(".,!?;:\"'()[]{}") for word in words}
    return any(word in bad_words for word in normalized if word)


def contains_blocked_links(text: str) -> bool:
    return bool(INVITE_PATTERN.search(text) or URL_PATTERN.search(text))
