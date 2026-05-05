from app.services.moderation_service import FloodTracker, contains_bad_words, contains_blocked_links


def test_contains_bad_words():
    assert contains_bad_words("This is scam", {"scam", "spam"})
    assert not contains_bad_words("This is clean", {"scam", "spam"})


def test_contains_blocked_links():
    assert contains_blocked_links("visit https://example.com")
    assert contains_blocked_links("join t.me/+abc123")
    assert not contains_blocked_links("hello world")


def test_flood_tracker_threshold():
    tracker = FloodTracker(flood_limit=2, flood_window_secs=30)
    assert not tracker.hit(1, 2)
    assert not tracker.hit(1, 2)
    assert tracker.hit(1, 2)
