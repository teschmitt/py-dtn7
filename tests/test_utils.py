from datetime import datetime, timezone

from py_dtn7 import from_dtn_timestamp, to_dtn_timestamp


def test_from_dtn_timestamp():
    ts: int = 4 * 3600 * 1000 + 20 * 60 * 1000
    correct_dt: datetime = datetime(
        year=2000, month=1, day=1, hour=4, minute=20, second=0, tzinfo=timezone.utc
    )
    assert from_dtn_timestamp(ts) == correct_dt


def test_to_dtn_timestamp():
    correct_ts: int = 4 * 3600 * 1000 + 20 * 60 * 1000
    dt: datetime = datetime(
        year=2000, month=1, day=1, hour=4, minute=20, second=0, tzinfo=timezone.utc
    )
    assert to_dtn_timestamp(dt) == correct_ts
