# ---- Nifty Futures paper desk config ----
# Strategy internals live here + in strategy.py; the dashboard never shows them.

DISPLAY_NAME = "Nifty Futures"        # the ONLY label shown publicly

CAPITAL  = 200000                     # INR paper capital
LOT_SIZE = 65                         # Nifty 50 futures units / lot (Jan 2026)
LOTS     = 1                          # trade size

# costs (per round-trip, per lot) — verify vs your contract note
ROUND_TRIP_COST_RS    = 455.0
SLIPPAGE_PTS_PER_SIDE = 1.0

# strategy params (private)
ST_PERIOD  = 10
ST_MULT_5M = 3.0
ST_MULT_15M = 3.0

# session (IST)
SESSION_OPEN = (9, 15)
SQUARE_OFF   = (15, 15)                # force flat + no new entries at/after this

INSTRUMENT_NAME = "NIFTY"             # front-month FUT resolved dynamically
