"""Inspect official historical NSE market-cap workbook without interpreting it as ranks."""
from io import BytesIO
import requests
import pandas as pd
from pathlib import Path

URL = "https://nsearchives.nseindia.com/web/sites/default/files/inline-files/MCAP31032022_1.xlsx"
r = requests.get(URL, timeout=90, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com/"})
print("FILE_URL",URL,"STATUS",r.status_code,"BYTES",len(r.content),"CONTENTTYPE",r.headers.get("Content-Type"))
r.raise_for_status()
if not r.content.startswith(b"PK"):
    raise ValueError("Download is not an XLSX workbook; refusing to parse page as ranking")
dest = Path("reports/v2/source_files")
dest.mkdir(parents=True, exist_ok=True)
(dest/"MCAP31032022_1.xlsx").write_bytes(r.content)
exc = pd.ExcelFile(BytesIO(r.content))
print("SHEETS:",exc.sheet_names)
for sheet in exc.sheet_names:
    df=pd.read_excel(exc,sheet_name=sheet,header=None,nrows=18)
    print(f"===== SHEET {sheet} =====")
    print(df.to_string(index=False,header=False,max_cols=20,max_colwidth=45))
