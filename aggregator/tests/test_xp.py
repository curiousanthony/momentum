from aggregator.xp import level_from_xp, xp_for_level, xp_progress_pct


def test_xp_for_level_monotonic():
    assert xp_for_level(1) < xp_for_level(2)
    assert xp_for_level(10) == int(100 * (10**1.5))


def test_level_from_xp_floor():
    assert level_from_xp(0) == 1
    assert level_from_xp(99) == 1
    assert level_from_xp(100) >= 1


def test_progress_pct():
    assert 0 <= xp_progress_pct(150, level_from_xp(150)) <= 100
