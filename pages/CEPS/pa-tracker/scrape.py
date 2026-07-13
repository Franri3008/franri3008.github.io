import csv
import html
import json
import os
import re

import requests

URL = "https://ideas.repec.org/top/top.belgium.html"
DIR = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(DIR, "data.csv")
META = os.path.join(DIR, "metadata.json")

page = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30).text

title = html.unescape(re.search(r"<h2[^>]*>(.*?)</h2>", page, re.S).group(1)).strip()

meta = json.load(open(META)) if os.path.exists(META) else {"title": None, "step": 0}
if title == meta["title"]:
    print(f"no update: title unchanged ({title!r})")
    raise SystemExit(0)

step = meta["step"] + 1

authors10 = page.split('id="authors10"')[1].split("</table>")[0]
rows = re.findall(r"<tr><td>(\d+)</td><td>\[(\d+)\]</td><td>(.*?)</td><td>([\d.]+)</td></tr>", authors10, re.S)
assert len(rows) >= 50, f"expected >=50 rows, got {len(rows)}"

new_file = not os.path.exists(DATA)
with open(DATA, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    if new_file:
        w.writerow(["step", "Rank", "W.Rank", "Author", "Institution", "City", "Country", "Score"])
    for rank, wrank, cell, score in rows[:50]:
        author = html.unescape(re.search(r'href="https://ideas\.repec\.org/[ef]/[^"]+">(.*?)</a>', cell, re.I).group(1))
        insts, cities, countries = [], [], []
        for link_text, trailing in re.findall(r"<small><a [^>]*>(.*?)</a>(.*?)</small>", cell, re.S):
            insts.append(html.unescape(link_text).replace("→", "->").strip())
            city, _, country = html.unescape(re.sub(r"<[^>]+>", "", trailing)).strip(" ,").rpartition(",")
            cities.append(city.strip())
            countries.append(country.strip())
        w.writerow([step, rank, wrank, author, "; ".join(insts), "; ".join(cities), "; ".join(countries), score])

titles = meta.get("titles", {})
titles[str(step)] = title
json.dump({"title": title, "step": step, "titles": titles}, open(META, "w"), indent=2)
print(f"step {step}: appended 50 rows ({title!r})")
