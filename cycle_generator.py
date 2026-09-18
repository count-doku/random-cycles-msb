r"""Generate a synthetic battery aging current profile.

The profile is a chain of symmetric charge/discharge cycles around a mid
state of charge (SoC). One cycle looks like this::

    SoC   /\
         /  \
             \    /
              \  /
               \/

    I   ___      ___
           |    |
           |____|

Each cycle starts and ends at the same SoC, so the profile is charge neutral
by construction. That is what makes it usable as a reference for the counter
in ``cycle_counter.py``: the counted depth of discharge must come back out of
the signal exactly as it was put in.

Running this module writes ``aging_profile.csv`` plus two plots.
"""

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

CAPACITY_AS = 7200.0  # Nominal capacity C_N in ampere seconds (2 Ah)
SAMPLE_TIME_S = 10.0  # Sample time of the generated profile
CURRENT_CHOICES_A = (1, 2, 3, 4)  # C-rates 0.5 C ... 2 C at C_N = 2 Ah
CYCLES_PER_SEGMENT = 600
PROFILE_CSV = Path("aging_profile.csv")

# Delta SoC of the first quarter cycle. The full cycle swings 0.5 up and
# 0.5 down, hence DoD = 1.0; the partial cycle swings 0.1, hence DoD = 0.2.
FULL_CYCLE_DSOC = 0.5
PARTIAL_CYCLE_DSOC = 0.1
PARTIAL_CYCLE_SHARE = 0.8  # Share of partial cycles in the mixed segment


class CoulombCounter:
    """Integrate current into charge, with coulombic efficiency and self discharge.

    Charge is counted in ampere seconds. Efficiency is applied on the charging
    direction only, because the loss happens when pushing charge in.
    """

    def __init__(self, init_value=0.0, eta=1.0, i_sd=0.0, capacity=CAPACITY_AS):
        self.charge = init_value  # Charge in As
        self.eta = eta  # Coulombic efficiency
        self.capacity = capacity  # Nominal capacity in As
        self.i_sd = i_sd  # Self discharge current in A

    def step(self, current, ts):
        """Integrate one sample and return the new charge and SoC."""
        if current >= 0:
            self.charge += self.eta * ts * current  # Charging
        else:
            self.charge += ts * current  # Discharging

        self.charge -= self.i_sd * ts

        return self.charge, self.soc

    @property
    def soc(self):
        """State of charge as a fraction of the nominal capacity."""
        return self.charge / self.capacity


def draw_cycle_depth(rng):
    """Draw the delta SoC of one cycle for the mixed segment."""
    if rng.random() < PARTIAL_CYCLE_SHARE:
        return PARTIAL_CYCLE_DSOC
    return FULL_CYCLE_DSOC


def create_cycle(current, delta_soc, ts, capacity=CAPACITY_AS):
    """Create the current samples of one symmetric cycle.

    The cycle runs up by ``delta_soc``, down by ``2 * delta_soc`` and back up
    by ``delta_soc``, so it returns to its starting SoC.

    Raises ``ValueError`` if the quarter cycle is not a whole number of
    samples, because a fractional sample would silently bias the charge
    balance and break the round trip through the counter.
    """
    quarter_duration = capacity / current * delta_soc  # Duration in s
    n_samples = quarter_duration / ts

    if not float(n_samples).is_integer():
        raise ValueError(
            "quarter cycle must be a whole number of samples, got "
            f"{n_samples} (I={current} A, dSoC={delta_soc}, ts={ts} s)"
        )

    n_samples = int(n_samples)
    return n_samples * [current] + 2 * n_samples * [-current] + n_samples * [current]


def create_profile(n_cycles, delta_soc, ts=SAMPLE_TIME_S, rng=None):
    """Chain ``n_cycles`` cycles of fixed depth with randomly drawn currents.

    Pass ``delta_soc=None`` to draw the depth per cycle as well, which gives
    the mixed segment.
    """
    rng = rng or np.random.default_rng()
    segments = []
    for _ in range(n_cycles):
        current = rng.choice(CURRENT_CHOICES_A)
        depth = draw_cycle_depth(rng) if delta_soc is None else delta_soc
        segments.append(create_cycle(current, depth, ts))
    return np.concatenate(segments)


def plot_profile(time, profile, ts, initial_charge=0.5 * CAPACITY_AS):
    """Plot the current profile and the SoC it produces."""
    fig, ax = plt.subplots(figsize=(15, 5))
    ax.plot(time, profile, drawstyle="steps-post", linewidth=0.1)
    ax.set(
        xlabel="time in s",
        ylabel="current in A",
        title=f"mean(I): {np.mean(profile):.3g} A",
    )
    fig.tight_layout()
    fig.savefig("current.png")

    counter = CoulombCounter(init_value=initial_charge)
    soc = []
    for current in profile:
        soc.append(counter.soc)
        counter.step(current, ts)

    fig, ax = plt.subplots(figsize=(15, 5))
    ax.plot(time, soc, linewidth=0.1)
    ax.set(xlabel="time in s", ylabel="SoC", title=f"mean(SoC): {np.mean(soc):.3g}")
    fig.tight_layout()
    fig.savefig("SoC.png")


def save_profile(time, profile, path=PROFILE_CSV):
    """Write the profile as a two column csv."""
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["time (s)", "current (A)"])
        writer.writerows(zip(time, profile, strict=True))


def build_aging_profile(ts=SAMPLE_TIME_S, n_cycles=CYCLES_PER_SEGMENT, rng=None):
    """Build the three segment aging profile used in the exercise.

    Segment 1: full cycles only.
    Segment 2: mixed, 20 % full and 80 % partial cycles.
    Segment 3: partial cycles only.

    The mixed segment is the interesting one: a counter that only looks at
    current sign changes cannot tell the two cycle depths apart there.
    """
    rng = rng or np.random.default_rng()
    return np.concatenate(
        [
            create_profile(n_cycles, FULL_CYCLE_DSOC, ts, rng),
            create_profile(n_cycles, None, ts, rng),
            create_profile(n_cycles, PARTIAL_CYCLE_DSOC, ts, rng),
        ]
    )


def main():
    profile = build_aging_profile()
    time = np.arange(len(profile)) * SAMPLE_TIME_S

    plot_profile(time, profile, SAMPLE_TIME_S)
    save_profile(time, profile)
    print(f"{len(profile)} samples written to {PROFILE_CSV}")


if __name__ == "__main__":
    main()
