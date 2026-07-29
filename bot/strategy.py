"""Private strategy logic — SuperTrend(5m) gated by SuperTrend(15m) trend filter.
Validated structure: enter with the trend, ride until the 5m SuperTrend flips.
Nothing here is ever written to the public dashboard."""
import pandas as pd
import numpy as np
from . import config as C


def _atr(df, n):
    pc = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"],
                    (df["high"] - pc).abs(),
                    (df["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def supertrend_dir(df, period, mult):
    hl2 = (df["high"] + df["low"]) / 2
    a = _atr(df, period)
    up = (hl2 + mult * a).to_numpy()
    lo = (hl2 - mult * a).to_numpy()
    c = df["close"].to_numpy()
    n = len(df)
    fu = np.full(n, np.nan); fl = np.full(n, np.nan); dr = np.ones(n, dtype=int)
    for i in range(n):
        if i == 0:
            fu[i] = up[i]; fl[i] = lo[i]; continue
        fu[i] = up[i] if (up[i] < fu[i - 1] or c[i - 1] > fu[i - 1]) else fu[i - 1]
        fl[i] = lo[i] if (lo[i] > fl[i - 1] or c[i - 1] < fl[i - 1]) else fl[i - 1]
        dr[i] = 1 if c[i] > fu[i - 1] else (-1 if c[i] < fl[i - 1] else dr[i - 1])
    return dr


def build_signals(bars5):
    """bars5: 5-min OHLC DataFrame indexed by tz-naive IST datetime.
    Returns bars5 with columns st5 (5m dir) and st15 (15m dir, ffilled)."""
    df = bars5.copy()
    df["st5"] = supertrend_dir(df, C.ST_PERIOD, C.ST_MULT_5M)
    b15 = df.resample("15min").agg({"open": "first", "high": "max",
                                    "low": "min", "close": "last"}).dropna()
    d15 = pd.Series(supertrend_dir(b15, C.ST_PERIOD, C.ST_MULT_15M), index=b15.index)
    df["st15"] = d15.reindex(df.index, method="ffill").fillna(0).astype(int)
    return df
