# AI MODEL LEADERBOARD SCRAPER & AGGREGATOR

## OVERVIEW

Automated system that scrapes three AI model leaderboards (LMArena, Artificial Analysis, LiveBench), 
matches model scores using a crosswalk mapping, and generates data.csv for the viz.

## QUICK START

#### 1. Install dependencies
pip install pandas beautifulsoup4 selenium webdriver-manager requests

#### 2. Run the update script
python update.py

#### 3. Find results in:
- data.csv (final aggregated scores)
- data/ folder (raw scraped data)

## FILE STRUCTURE

update.py           Main script - scrapes & builds processed.csv in one run
data/processed.csv  Output file - aggregated scores for all models
metadata.json       Metadata about the last run (timestamp, stats)
alerts.txt          Text report of top-performing potential new models
config/             Configuration files
  ├── tracking.json Model configuration & name mapping (JSON)
  ├── models.json   Organization details (colors, logos)
data/scraped/       Raw scraped CSV files from each leaderboard
  ├── lmarena_text_leaderboard.csv
  ├── aa_models_leaderboard.csv
  └── livebench_leaderboard.csv

## HOW IT WORKS

#### 1. SCRAPING PHASE
- LMArena: HTTP request with BeautifulSoup parsing
- Artificial Analysis: Selenium (JavaScript-rendered table)
- LiveBench: Selenium with complex rowspan/colspan handling
- Saves raw files to `data/scraped/`

#### 2. MATCHING PHASE
- Reads config/tracking.json which contains model metadata AND lookup keys
- Searches each scraped dataset for matching models using the lookup keys
- Extracts relevant score columns (Elo, Quality Index, Average)

#### 3. OUTPUT PHASE
- Combines matched scores with base structure from tracking.json
- Generates `data/processed.csv` with format: model;name;logo;lma;aa;lb
- Generates metadata.json (stats) and alerts.txt (alerts)

## CONFIGURATION (config/tracking.json)

Format: List of JSON objects

Fields:
- model: Internal model ID
- name: Display Name
- logo: Logo ID (matches models.json)
- lma_lookup: Model name as it appears on LMArena
- aa_lookup: Model name on Artificial Analysis
- lb_lookup: Model name on LiveBench

## ADDING NEW MODELS
1. Add a new object to the `config/tracking.json` list:
   ```json
   {
       "model": "new-model-id",
       "name": "Display Name",
       "logo": "org-logo-id",
       "lma_lookup": "LMArena Name",
       "aa_lookup": "AA Name",
       "lb_lookup": "LiveBench Name"
   }
   ```

2. (Optional) If this is a new organization, add to `config/models.json`
   Add a new entry for the logo/color mapping used in "logo" field.

3. Run the update script:
   `python update.py`

## SCORE TYPES

- lma: LMArena Elo rating (integer, ~1200-1500)
- aa: Artificial Analysis Quality Index (integer, 0-100)
- lb: LiveBench Average score (float, 0-100)

## LEGACY FILES
scraper.py          Standalone scraper (now part of update.py)
build_fixed.py      Standalone builder (now part of update.py)
fixed_testing.csv   Old output file (replaced by data.csv)

Keep for reference or delete - update.py replaces both.

## LAST UPDATED

2025-12-31