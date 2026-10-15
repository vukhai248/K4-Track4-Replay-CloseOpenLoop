"""Step 2: scenarios. Metrics (TTC, required deceleration), mining braking events from the logs, and the physics
frontier that separates 'no planner could have avoided this' from 'this planner failed'."""
import numpy as np

from . import config as C


def ttc(gap, closing):
    """Time to collision [s] = gap / closing speed (inf when the gap is not closing)."""
    gap, closing = np.broadcast_arrays(np.asarray(gap, float), np.asarray(closing, float))
    closing_in = closing > 0
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where(closing_in, gap / np.where(closing_in, closing, 1.0), np.inf)
    return t


def required_decel(gap, closing):
    """Deceleration [m/s^2] needed to remove the closing speed exactly at contact: closing^2 / (2 gap)."""
    gap, closing = np.broadcast_arrays(np.asarray(gap, float), np.asarray(closing, float))
    needed = (closing > 0) & (gap > 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        b = np.where(needed, closing ** 2 / (2.0 * np.where(needed, gap, 1.0)), 0.0)
    return b


def unavoidable(gaps, dvs, t_react=0.0, b_max=C.B_MAX):
    """Boolean grid (len(dvs), len(gaps)): True where NO planner can avoid contact, even braking at b_max after the
    reaction delay: gap < dv * t_react + dv^2 / (2 b_max)  (lead keeps its speed)."""
    gaps, dvs = np.asarray(gaps, float), np.asarray(dvs, float)
    G, DV = np.meshgrid(gaps, dvs)                       # (len(dvs), len(gaps))
    # during t_react the gap still closes at dv m/s; then full braking needs dv^2 / (2 b_max) metres
    return DV * t_react + DV ** 2 / (2.0 * b_max) > G


def _first_long_run(mask, min_steps):
    """(start, end) of the first run of at least `min_steps` True values in `mask`, or None."""
    idx = np.flatnonzero(mask)
    if len(idx) < min_steps:
        return None
    brk = np.flatnonzero(np.diff(idx) > 1)               # indices where the run breaks
    starts = np.r_[idx[0], idx[brk + 1]]
    ends = np.r_[idx[brk], idx[-1]]
    long = np.flatnonzero(ends - starts + 1 >= min_steps)
    return (int(starts[long[0]]), int(ends[long[0]])) if len(long) else None


def mine_braking(logs, threshold=C.BRAKE_THRESHOLD, min_steps=5):
    """Find trajectories where the lead brakes: smoothed deceleration below `threshold` for at least `min_steps`
    consecutive steps (0.5 s). Returns a list of event dicts (one per trajectory, first event only)."""
    out = []
    for i in range(len(logs)):
        a = logs.a_lead[i, :logs.n[i]]                   # smoothed lead deceleration, NOT Acc_LV
        run = _first_long_run(a < threshold, min_steps)
        if run is None:
            continue
        s, e = run
        out.append({"traj": int(i), "onset_step": s, "peak_decel": float(np.min(a[s:e + 1])),
                    "gap_m": float(logs.gap[i, s]),
                    "closing_m_s": float(logs.v_ego[i, s] - logs.v_lead_s[i, s]),
                    "ego_speed": float(logs.v_ego[i, s])})
    return out


def human_brake_limit(logs, q=0.1):
    """Hardest braking [m/s^2, positive number] that the logged human followers ever applied (the q-th percentile of
    their acceleration, from the speed differences). Learned planners cannot have seen anything harder."""
    a = np.diff(logs.v_ego, axis=1) / C.DT
    return float(-np.nanpercentile(a, q))


def grid_from_logs(logs, v_ego, n_gap=60, n_dv=45):
    """Scenario grid. Gap limits come from what the logs contain (p2 .. p98 of the logged gaps). Closing speed runs
    from 0 to v_ego: dv = v_ego means the cutter is standing still, the most extreme case (never faster than that,
    otherwise the cutter would drive backwards)."""
    g_lo, g_hi = np.nanpercentile(logs.gap, [2, 98])
    return np.linspace(g_lo, g_hi, n_gap), np.linspace(0.0, v_ego, n_dv)
