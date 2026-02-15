import requests
from bs4 import BeautifulSoup
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

NEPSE_URL = "https://nepalstock.com"


def fetch_live_prices() -> dict:
    """
    Fetches live prices for all stocks listed on NEPSE (LTP).
    Returns:
        { "NABIL": 542.3, "NLIC": 815.0, ... }

    NOTE:
    SSL verification is disabled due to common NEPSE SSL certificate issues.
    """

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    })

    try:
        response = session.get(NEPSE_URL, timeout=20, verify=False)
    except Exception as e:
        raise ConnectionError(f"Failed to connect to NEPSE: {e}")

    if response.status_code != 200:
        raise ConnectionError(f"Failed to fetch NEPSE homepage: {response.status_code}")

    soup = BeautifulSoup(response.text, "lxml")

    # Find Today's Price link
    link = soup.find("a", string=re.compile("Today's Price", re.IGNORECASE))

    if not link or not link.get("href"):
        raise ValueError("Could not locate Today's Price link. NEPSE website layout changed.")

    todays_price_url = NEPSE_URL + link["href"]

    price_page = session.get(todays_price_url, timeout=20, verify=False)

    if price_page.status_code != 200:
        raise ConnectionError(f"Failed to fetch Today's Price page: {price_page.status_code}")

    soup_price = BeautifulSoup(price_page.text, "lxml")

    table = soup_price.find("table")
    if not table:
        raise ValueError("Price table not found. NEPSE page structure may have changed.")

    rows = table.find_all("tr")

    prices = {}

    for row in rows[1:]:
        cols = row.find_all("td")

        if len(cols) < 6:
            continue

        symbol = cols[1].get_text(strip=True).upper()
        ltp_text = cols[5].get_text(strip=True)

        try:
            ltp = float(ltp_text.replace(",", ""))
        except Exception:
            continue

        prices[symbol] = ltp

    if not prices:
        raise ValueError("No prices extracted. NEPSE site HTML may have changed.")

    return prices
