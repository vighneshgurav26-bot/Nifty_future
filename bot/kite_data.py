"""Kite data access — resolve the Nifty front-month FUT and pull recent 5-min bars.
Runtime only needs KITE_API_KEY + KITE_ACCESS_TOKEN (secret stays on your PC)."""
import os
from datetime import datetime, timedelta
import pandas as pd
from kiteconnect import KiteConnect
from . import config as C

IST = "Asia/Kolkata"


def _kite():
    api_key = os.environ["KITE_API_KEY"]
    token = os.environ["KITE_ACCESS_TOKEN"]
    k = KiteConnect(api_key=api_key)
    k.set_access_token(token)
    return k


def front_month_token(k):
    inst = pd.DataFrame(k.instruments("NFO"))
    fut = inst[(inst["name"] == C.INSTRUMENT_NAME) &
               (inst["instrument_type"] == "FUT")].copy()
    fut["expiry"] = pd.to_datetime(fut["expiry"])
    today = pd.Timestamp(datetime.now()).normalize()
    fut = fut[fut["expiry"] >= today].sort_values("expiry")
    row = fut.iloc[0]
    return int(row["instrument_token"]), row["tradingsymbol"]


def recent_5min(k, token, days=5):
    end = datetime.now()
    start = end - timedelta(days=days)
    data = k.historical_data(token, start, end, "5minute")
    df = pd.DataFrame(data)
    if df.empty:
        return df
    df = df.rename(columns={"date": "dt"}).set_index("dt")
    # to tz-naive IST so session times compare correctly
    if df.index.tz is not None:
        df.index = df.index.tz_convert(IST).tz_localize(None)
    return df[["open", "high", "low", "close"]].sort_index()
