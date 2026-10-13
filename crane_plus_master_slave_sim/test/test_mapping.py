import pytest

from crane_plus_master_slave_sim.mapping import map_targets, step_towards


def test_map_targets_invert_and_offset():
    leader = {'a': 0.5, 'b': -0.2}
    assert map_targets(leader, ['a', 'b'], [False, True], [0.0, 0.1]) == pytest.approx([0.5, 0.3])


def test_map_targets_missing_joint():
    assert map_targets({'a': 0.5}, ['a', 'b'], [False, False], [0.0, 0.0]) is None


def test_step_limits_speed_and_range():
    out = step_towards([0.0, 0.0], [1.0, -5.0], [-1.0, -1.0], [1.0, 1.0], 0.03)
    assert out == pytest.approx([0.03, -0.03])
    out = step_towards([0.99, -0.99], [5.0, -5.0], [-1.0, -1.0], [1.0, 1.0], 0.03)
    assert out == pytest.approx([1.0, -1.0])
