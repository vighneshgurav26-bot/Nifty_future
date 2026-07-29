"""Paper account + deterministic catch-up replay.
Processes every CLOSED 5-min bar after the last one we saw, so skipped
GitHub-Actions runs never desync the account. One position at a time.
Entries/exits fill at the bar close, worsened by slippage; round-trip cost applied."""
import json, os
from datetime import time
from . import config as C
from .strategy import build_signals

STATE_PATH = "state.json"


def fresh_state():
    return {"capital": C.CAPITAL, "realized": 0.0, "position": None,
            "last_bar": None, "trades": [], "equity_curve": []}


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            return json.load(f)
    return fresh_state()


def save_state(s):
    with open(STATE_PATH, "w") as f:
        json.dump(s, f, indent=2, default=str)


def _fill(price, direction, is_entry):
    slip = C.SLIPPAGE_PTS_PER_SIDE
    # entry: pay worse; exit: receive worse
    if is_entry:
        return price + direction * slip
    return price - direction * slip


def _units():
    return C.LOT_SIZE * C.LOTS


def _open(state, direction, price, t):
    state["position"] = {"dir": direction, "entry": _fill(price, direction, True),
                         "entry_time": t.isoformat()}


def _close(state, price, t, reason):
    p = state["position"]; d = p["dir"]
    exitpx = _fill(price, d, False)
    gross = (exitpx - p["entry"]) * d * _units()
    net = gross - C.ROUND_TRIP_COST_RS
    state["realized"] += net
    state["trades"].append({
        "entry_time": p["entry_time"], "exit_time": t.isoformat(),
        "dir": "LONG" if d == 1 else "SHORT",
        "entry": round(p["entry"], 2), "exit": round(exitpx, 2),
        "net": round(net, 1), "reason": reason})
    state["equity_curve"].append([t.isoformat(),
                                  round(C.CAPITAL + state["realized"], 1)])
    state["position"] = None


def replay(state, bars5):
    """Advance the paper account across all closed bars newer than last_bar."""
    df = build_signals(bars5)
    df = df.dropna(subset=["st5"])
    open_t = time(*C.SESSION_OPEN)
    off_t = time(*C.SQUARE_OFF)
    last = state.get("last_bar")
    for ts, row in df.iterrows():
        if last is not None and ts.isoformat() <= last:
            continue
        t = ts.to_pydatetime()
        tt = t.time()
        px = float(row["close"])
        pos = state["position"]
        # ---- manage open position ----
        if pos is not None:
            if pos["dir"] != int(row["st5"]) or tt >= off_t:
                _close(state, px, t, "flip" if tt < off_t else "squareoff")
                pos = None
        # ---- new entry (only inside session, before square-off) ----
        if pos is None and open_t <= tt < off_t:
            if int(row["st5"]) == 1 and int(row["st15"]) == 1:
                _open(state, 1, px, t)
            elif int(row["st5"]) == -1 and int(row["st15"]) == -1:
                _open(state, -1, px, t)
        state["last_bar"] = ts.isoformat()
    return state


def mark_to_market(state, last_price):
    eq = C.CAPITAL + state["realized"]
    pos = state["position"]
    if pos is not None and last_price is not None:
        eq += (last_price - pos["entry"]) * pos["dir"] * _units()
    return eq
