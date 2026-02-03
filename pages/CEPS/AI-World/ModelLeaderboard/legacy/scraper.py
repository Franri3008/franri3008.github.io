import random
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

STRIP_SELECTORS = "svg,img,picture,source,use,i,[aria-hidden='true'],*[hidden],.sr-only,.sr_only,.srOnly,.visually-hidden,[class*='icon'],i[class*='fa-']"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
]

def print_step(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = ">>>" if level == "INFO" else "***"
    print(f"\n{prefix} [{timestamp}] {message}")

def clean_text(tag):
    clone = BeautifulSoup(str(tag), "html.parser")
    for el in clone.select(STRIP_SELECTORS):
        el.decompose()
    return " ".join(clone.stripped_strings)

def get_chrome_driver(headless=True):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)

def extract_table_data(table, skip_first_empty=False):
    thead = table.find("thead")
    header_cells = thead.select("tr")[-1].find_all("th") if thead and thead.select("tr") else table.select("tr th")
    headers = [clean_text(th) for idx, th in enumerate(header_cells) if not (skip_first_empty and idx == 0 and clean_text(th) == "")]

    tbody = table.find("tbody") or table
    rows = []
    for tr in tbody.find_all("tr", recursive=False):
        cells = tr.find_all(["td", "th"], recursive=False)
        if not cells:
            continue
        row = [clean_text(td) for idx, td in enumerate(cells) if not (skip_first_empty and idx == 0 and clean_text(td) == "")]
        if len(row) != len(headers):
            row = (row + [""] * len(headers))[:len(headers)]
        rows.append(row)
    return pd.DataFrame(rows, columns=headers)

# ============================================================================
# START SCRAPING
# ============================================================================
print("=" * 80)
print_step(f"STARTING LEADERBOARD SCRAPER", "START")
print("=" * 80)

# Create data directory if it doesn't exist
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)
print_step(f"Data directory: {data_dir.absolute()}")

# 1. LMArena Text Leaderboard
print_step("[1/3] Starting LMArena Text Leaderboard scraper")
print_step("Fetching page with requests...")
resp = requests.get("https://lmarena.ai/leaderboard/text", headers={
    "User-Agent": USER_AGENTS[0], "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache", "Pragma": "no-cache"
}, timeout=30)
resp.raise_for_status()
print_step("Parsing HTML and extracting table...")
soup = BeautifulSoup(resp.text, "html.parser")
table = soup.select_one("table.w-full.caption-bottom.text-sm")
if not table:
    raise ValueError("LMArena table not found")
df = extract_table_data(table)
print_step(f"Extracted {len(df)} rows, {len(df.columns)} columns")
output_file = data_dir / "lmarena_text_leaderboard.csv"
df.to_csv(output_file, index=False)
print_step(f"✓ Saved: {output_file}", "SUCCESS")

# 2. Artificial Analysis Models Leaderboard
print_step("[2/3] Starting Artificial Analysis Models Leaderboard scraper")
print_step("Launching headless Chrome browser...")
driver = get_chrome_driver()
print_step("Loading page and waiting for table to render...")
driver.get("https://artificialanalysis.ai/leaderboards/models?deprecation=all")
WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.w-full.caption-bottom.text-sm.rounded")))
print_step("Parsing rendered HTML...")
soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()
table = soup.select_one("table.w-full.caption-bottom.text-sm.rounded")
if not table:
    raise RuntimeError("ArtificialAnalysis table not found")
df = extract_table_data(table, skip_first_empty=True)
print_step(f"Extracted {len(df)} rows, {len(df.columns)} columns")
output_file = data_dir / "aa_models_leaderboard.csv"
df.to_csv(output_file, index=False)
print_step(f"✓ Saved: {output_file}", "SUCCESS")

# 3. LiveBench Leaderboard
print_step("[3/3] Starting LiveBench Leaderboard scraper")
print_step("Launching headless Chrome browser...")
driver = get_chrome_driver()
try:
    print_step("Loading page and waiting for table to render...")
    driver.get("https://livebench.ai/#/")
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.main-tabl.table")))
    table_el = driver.find_element(By.CSS_SELECTOR, "table.main-tabl.table")
    print_step("Scrolling table to ensure all content is loaded...")
    driver.execute_script("arguments[0].parentElement.scrollLeft=arguments[0].parentElement.scrollWidth", table_el)

    print_step("Parsing complex table with rowspan/colspan...")
    soup = BeautifulSoup(table_el.get_attribute("outerHTML"), "html.parser")
    thead = soup.find("thead")
    header_rows = thead.find_all("tr") if thead else []

    # Build header matrix from rowspan/colspan cells
    grid, spans = [], {}
    for tr in header_rows:
        row = []
        for cell in tr.find_all(["th", "td"]):
            row.append({"text": cell.get_text(strip=True), "colspan": int(cell.get("colspan", 1)), "rowspan": int(cell.get("rowspan", 1))})
        grid.append(row)

    header_matrix = []
    for r_idx in range(len(grid)):
        row_out, col_idx = [], 0
        for cell in grid[r_idx]:
            while (r_idx, col_idx) in spans:
                row_out.append(spans[(r_idx, col_idx)])
                col_idx += 1
            for _ in range(cell["colspan"]):
                row_out.append(cell["text"])
            if cell["rowspan"] > 1:
                for r in range(1, cell["rowspan"]):
                    for i in range(cell["colspan"]):
                        spans[(r_idx + r, col_idx + i)] = cell["text"]
            col_idx += cell["colspan"]
        header_matrix.append(row_out)

    max_cols = max(len(r) for r in header_matrix) if header_matrix else 0
    headers = [" | ".join(filter(None, [header_matrix[r][c] if c < len(header_matrix[r]) else "" for r in range(len(header_matrix))])) or f"col_{c+1}" for c in range(max_cols)]

    tbody = soup.find("tbody")
    data = [[td.get_text(strip=True) for td in tr.find_all(["td", "th"])] for tr in (tbody.find_all("tr") if tbody else [])]
    for row in data:
        if len(row) < len(headers):
            row += [""] * (len(headers) - len(row))

    df = pd.DataFrame(data, columns=headers)
    print_step(f"Extracted {len(df)} rows, {len(df.columns)} columns")
    output_file = data_dir / "livebench_leaderboard.csv"
    df.to_csv(output_file, index=False)
    print_step(f"✓ Saved: {output_file}", "SUCCESS")
finally:
    driver.quit()

# ============================================================================
# COMPLETION
# ============================================================================
print("\n" + "=" * 80)
print_step("ALL SCRAPERS COMPLETED SUCCESSFULLY!", "SUCCESS")
print("=" * 80)
