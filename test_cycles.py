"""Round trip check: what the generator puts into a profile, the counter gets back.

This is the one property worth guarding. Both modules encode the same cycle
definition, and a change to either that breaks that agreement is a real bug.
"""

import numpy as np
import pytest

from cycle_counter import CAPACITY_AS, SAMPLE_TIME_S, CycleCounter, count_profile
from cycle_generator import build_aging_profile, create_cycle


def test_cycle_is_charge_neutral():
    cycle = create_cycle(current=2, delta_soc=0.5, ts=SAMPLE_TIME_S)
    assert np.isclose(np.sum(cycle) * SAMPLE_TIME_S, 0.0)


def test_cycle_rejects_fractional_samples():
    with pytest.raises(ValueError, match="whole number of samples"):
        create_cycle(current=7, delta_soc=0.5, ts=SAMPLE_TIME_S)


@pytest.mark.parametrize(("delta_soc", "expected_dod"), [(0.5, 1.0), (0.1, 0.2)])
def test_counter_recovers_generated_depth(delta_soc, expected_dod):
    cycle = create_cycle(current=1, delta_soc=delta_soc, ts=SAMPLE_TIME_S)
    counter = CycleCounter()
    n_cycles, dod, _ = counter.count_cycle(
        0.5 * CAPACITY_AS, np.array(cycle), SAMPLE_TIME_S
    )
    assert n_cycles == 1
    assert np.isclose(dod, expected_dod)


def test_counter_reports_no_cycle_on_truncated_profile():
    cycle = create_cycle(current=1, delta_soc=0.5, ts=SAMPLE_TIME_S)
    truncated = np.array(cycle[: len(cycle) // 2])
    counter = CycleCounter()
    assert counter.count_cycle(0.5 * CAPACITY_AS, truncated, SAMPLE_TIME_S) is None


def test_counter_finds_every_generated_cycle():
    rng = np.random.default_rng(0)
    n_per_segment = 5
    profile = build_aging_profile(n_cycles=n_per_segment, rng=rng)

    full, partial, _, capacity_log = count_profile(profile)

    assert full + partial == 3 * n_per_segment
    assert full >= n_per_segment  # Segment 1 is full cycles by construction
    assert partial >= n_per_segment  # Segment 3 is partial cycles
    assert np.all(np.diff(capacity_log) < 0)  # Capacity only ever fades
