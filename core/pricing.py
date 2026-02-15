import requests
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://nepalstock.com.np"
API_BASE = "https://nepalstock.com.np/api"


def _get_session():
    s = requests.Session()
    s.verify = False

    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json, text/plain, */*",
        "Referer": BASE_URL + "/",
        "Origin": BASE_URL
    })
    return s


def _try_token_endpoints(session: requests.Session) -> str:
    """
    NEPSE has changed token endpoints many times.
    This function tries multiple endpoints and returns token if found.
    """

    token_endpoints = [
        f"{API_BASE}/auth/token",
        f"{API_BASE}/auth/access-token",
        f"{API_BASE}/authenticate/token",
        f"{API_BASE}/authenticate/prove",
        f"{API_BASE}/authenticate",
    ]

    for url in token_endpoints:
        try:
            r = session.get(url, timeout=20)

            if r.status_code != 200:
                continue

            # Try JSON token extraction
            try:
                data = r.json()
                token = (
                    data.get("accessToken")
                    or data.get("token")
                    or data.get("access_token")
                    or data.get("access-token")
                )
                if token:
                    return token
            except Exception:
                pass

            # Try token in headers
            token = r.headers.get("Authorization") or r.headers.get("access-token")
            if token:
                token = token.replace("Bearer", "").strip()
                return token

        except Exception:
            continue

    raise ConnectionError("Could not generate NEPSE token (all token endpoints failed).")


def fetch_live_prices() -> dict:
    """
    Fetch live NEPSE prices using authenticated API calls.
    Returns dict: {symbol: ltp}
    """

    session = _get_session()

    # Step 1: Visit homepage to set cookies
    home = session.get(BASE_URL, timeout=20)
    if home.status_code != 200:
        raise ConnectionError(f"Failed to load NEPSE homepage: {home.status_code}")

    # Step 2: Get token
    token = _try_token_endpoints(session)

    # Step 3: Try different auth header styles (NEPSE changes frequently)
    auth_header_variants = [
        {"Authorization": f"Bearer {token}"},
        {"authorization": f"Bearer {token}"},
        {"access-token": token},
        {"Access-Token": token},
        {"token": token}
    ]

    # Step 4: Price endpoints (NEPSE also changes frequently)
    price_endpoints = [
        f"{API_BASE}/nots/securityDailyTradeStat",
        f"{API_BASE}/nots/securityDailyTradeStat/58",
        f"{API_BASE}/nots/securityDailyTradeStat/0",
    ]

    last_status = None

    for auth_headers in auth_header_variants:
        for endpoint in price_endpoints:
            try:
                r = session.get(endpoint, headers=auth_headers, timeout=25)

                last_status = r.status_code

                if r.status_code != 200:
                    continue

                data = r.json()

                # Sometimes response is {"data":[...]}
                if isinstance(data, dict) and "data" in data:
                    data = data["data"]

                if not isinstance(data, list):
                    continue

                prices = {}

                for row in data:
                    try:
                        symbol = str(row.get("symbol", "")).strip().upper()
                        ltp = row.get("lastTradedPrice", None)

                        if symbol and ltp is not None:
                            ltp = float(ltp)
                            if ltp > 0:
                                prices[symbol] = ltp
                    except Exception:
                        continue

                if prices:
                    return prices

            except Exception:
                continue

    raise ConnectionError(f"NEPSE price API failed. Last status code: {last_status}")
