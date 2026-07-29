"""RUN THIS ON YOUR PC EACH MORNING (Kite access tokens expire ~7:30am IST).
It prints an access token — paste it into the repo secret KITE_ACCESS_TOKEN.

    pip install kiteconnect
    python get_token.py
"""
from kiteconnect import KiteConnect

API_KEY    = "PASTE_YOUR_API_KEY"
API_SECRET = "PASTE_YOUR_API_SECRET"   # stays on your PC only — never goes to GitHub

kite = KiteConnect(api_key=API_KEY)
print("\n1) Open this link, log in:\n   ", kite.login_url())
rt = input("\n2) Paste the request_token from the redirect URL (only the code after request_token=): ").strip()
data = kite.generate_session(rt, api_secret=API_SECRET)
print("\n=== KITE_ACCESS_TOKEN (copy this into the GitHub secret) ===")
print(data["access_token"])
print("============================================================\n")
