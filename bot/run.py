"""Entry point — run every 5 min during market hours via GitHub Actions.
Fetches recent bars, advances the paper account, writes the PUBLIC dashboard
data (name + numbers only — no strategy details)."""
import json, os, sys
from datetime import datetime, time
from zoneinfo import ZoneInfo
from . import config as C
from . import engine

IST = ZoneInfo("Asia/Kolkata")


def within_market_hours(now_ist):
    if now_ist.weekday() >= 5:          # Sat/Sun
        return False
    t = now_ist.time()
    return time(9, 10) <= t <= time(15, 40)


def write_dashboard(state, last_price, symbol):
    eq = engine.mark_to_market(state, last_price)
    pnl = eq - C.CAPITAL
    trades = state["trades"]
    wins = [t for t in trades if t["net"] > 0]
    wr = round(100 * len(wins) / len(trades), 1) if trades else 0.0
    status = "IN TRADE" if state["position"] else "FLAT"
    data = {                                   # <-- PUBLIC. No strategy fields.
        "name": C.DISPLAY_NAME,
        "capital": C.CAPITAL,
        "equity": round(eq, 1),
        "pnl": round(pnl, 1),
        "pnl_pct": round(100 * pnl / C.CAPITAL, 2),
        "trades": len(trades),
        "win_rate": wr,
        "status": status,
        "updated": datetime.now(IST).strftime("%Y-%m-%d %H:%M IST"),
        "equity_curve": state["equity_curve"][-500:],
    }
    os.makedirs("docs", exist_ok=True)
    with open("docs/data.json", "w") as f:
        json.dump(data, f, indent=2)


def main():
    now = datetime.now(IST)
    state = engine.load_state()

    if not within_market_hours(now):
        # keep the dashboard timestamp fresh, do nothing else
        write_dashboard(state, None, None)
        engine.save_state(state)
        print("outside market hours — no action")
        return

    from .kite_data import _kite, front_month_token, recent_5min
    k = _kite()
    token, symbol = front_month_token(k)
    bars = recent_5min(k, token, days=5)
    if bars.empty:
        print("no bars returned"); write_dashboard(state, None, symbol); return

    engine.replay(state, bars)
    last_price = float(bars["close"].iloc[-1])
    write_dashboard(state, last_price, symbol)
    engine.save_state(state)
    p = state["position"]
    print(f"{symbol}  last={last_price}  pos={'FLAT' if not p else p['dir']}  "
          f"trades={len(state['trades'])}  realized={round(state['realized'],1)}")


if __name__ == "__main__":
    main()
