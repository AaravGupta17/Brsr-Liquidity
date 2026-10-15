"""Diagnostic probe for NSE's official historical market-cap download URL.

Log only page download links and 2022-era context. Does not scrape prices.
"""
from html.parser import HTMLParser
import re
import requests

URL = "https://www.nseindia.com/static/regulations/listing-compliance/nse-market-capitalisation-all-companies"

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            a = dict(attrs)
            self.links.append(a.get("href", ""))

s = requests.Session()
h = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36",
     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
     "Accept-Language": "en-US,en;q=0.9"}
for path in ["https://www.nseindia.com/", URL]:
    try:
        response = s.get(path, timeout=30, headers=h)
        print(f"URL={path} status={response.status_code} bytes={len(response.content)} final={response.url}")
        if path != URL: continue
        txt = response.text
        for term in ["March 31, 2022", "Mar 31, 2022", "2022", "market-cap", ".xls"]:
            print(f"term={term} position={txt.lower().find(term.lower())}")
        l = Links(); l.feed(txt)
        matches = [x for x in l.links if re.search(r"2022|\.xls|market.?cap|capital", x, re.I)]
        for x in matches[:90]: print("LINK", x[:600])
        for m in list(re.finditer("2022", txt, re.I))[:25]:
            print("CONTEXT", re.sub(r"\\s+", " ", txt[max(0,m.start()-230):m.end()+300])[:700])
    except Exception as exc:
        print(f"ERROR {path} {type(exc).__name__}: {exc}")
