import pandas as pd
from datetime import datetime
from pathlib import Path

def print_step(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = ">>>" if level == "INFO" else "***"
    print(f"\n{prefix} [{timestamp}] {message}")

print("=" * 80)
print_step("BUILDING DATA.CSV", "START")
print("=" * 80)

# Set up data directory
data_dir = Path("data")
print_step(f"Reading scraped data from: {data_dir.absolute()}")

# Read crosswalk for model name mappings
print_step("Reading crosswalk.csv...")
crosswalk = pd.read_csv("crosswalk.csv")
print_step(f"Loaded {len(crosswalk)} model mappings")

# Read existing fixed.csv to get the base structure (model names, display names, logos)
print_step("Reading fixed.csv for base structure...")
fixed_base = pd.read_csv("fixed.csv", sep=";")
print_step(f"Loaded {len(fixed_base)} models from fixed.csv")

# Initialize the result dataframe with base data
result = fixed_base[['model', 'name', 'logo']].copy()
result['lma'] = None
result['aa'] = None
result['lb'] = None

# Try to read scraped data (may not exist yet)
print_step("Reading scraped leaderboard data...")

try:
    lma_data = pd.read_csv(data_dir / "lmarena_text_leaderboard.csv")
    print_step(f"✓ Loaded LMArena data: {len(lma_data)} rows")
except FileNotFoundError:
    print_step("⚠ data/lmarena_text_leaderboard.csv not found, skipping LMArena scores")
    lma_data = None

try:
    aa_data = pd.read_csv(data_dir / "aa_models_leaderboard.csv")
    print_step(f"✓ Loaded Artificial Analysis data: {len(aa_data)} rows")
except FileNotFoundError:
    print_step("⚠ data/aa_models_leaderboard.csv not found, skipping AA scores")
    aa_data = None

try:
    lb_data = pd.read_csv(data_dir / "livebench_leaderboard.csv")
    print_step(f"✓ Loaded LiveBench data: {len(lb_data)} rows")
except FileNotFoundError:
    print_step("⚠ data/livebench_leaderboard.csv not found, skipping LiveBench scores")
    lb_data = None

# Process each model in the result dataframe
print_step("Matching models and extracting scores...")
matches_found = {'lma': 0, 'aa': 0, 'lb': 0}

for idx, row in result.iterrows():
    model_id = row['model']

    # Find this model in crosswalk
    crosswalk_row = crosswalk[crosswalk['aiw'] == model_id]

    if crosswalk_row.empty:
        continue

    crosswalk_row = crosswalk_row.iloc[0]

    # Extract LMArena score
    if lma_data is not None and pd.notna(crosswalk_row['lma']) and crosswalk_row['lma']:
        lma_name = crosswalk_row['lma']
        # Look for model in LMArena data (typically in "Model" column with "Arena Score" or "Elo")
        for col in lma_data.columns:
            if 'model' in col.lower():
                model_col = col
                break
        else:
            model_col = lma_data.columns[0]  # Use first column if no "model" found

        lma_match = lma_data[lma_data[model_col].str.contains(lma_name, case=False, na=False, regex=False)]
        if not lma_match.empty:
            # Find score column (Arena Score, Elo, Rating, etc.)
            for col in lma_data.columns:
                if any(keyword in col.lower() for keyword in ['arena', 'elo', 'score', 'rating']):
                    score = lma_match.iloc[0][col]
                    try:
                        result.at[idx, 'lma'] = int(float(score))
                        matches_found['lma'] += 1
                    except (ValueError, TypeError):
                        pass
                    break

    # Extract Artificial Analysis score
    if aa_data is not None and pd.notna(crosswalk_row['aa']) and crosswalk_row['aa']:
        aa_name = crosswalk_row['aa']
        # Look for model in AA data
        for col in aa_data.columns:
            if 'model' in col.lower() or 'name' in col.lower():
                model_col = col
                break
        else:
            model_col = aa_data.columns[0]

        aa_match = aa_data[aa_data[model_col].str.contains(aa_name, case=False, na=False, regex=False)]
        if not aa_match.empty:
            # Find quality score column
            for col in aa_data.columns:
                if any(keyword in col.lower() for keyword in ['quality', 'score', 'index']):
                    score = aa_match.iloc[0][col]
                    try:
                        result.at[idx, 'aa'] = int(float(score))
                        matches_found['aa'] += 1
                    except (ValueError, TypeError):
                        pass
                    break

    # Extract LiveBench score
    if lb_data is not None and pd.notna(crosswalk_row['lb']) and crosswalk_row['lb']:
        lb_name = crosswalk_row['lb']
        # Look for model in LiveBench data
        for col in lb_data.columns:
            if 'model' in col.lower():
                model_col = col
                break
        else:
            model_col = lb_data.columns[0]

        lb_match = lb_data[lb_data[model_col].str.contains(lb_name, case=False, na=False, regex=False)]
        if not lb_match.empty:
            # Find average or overall score column
            for col in lb_data.columns:
                if any(keyword in col.lower() for keyword in ['average', 'overall', 'total', 'score']):
                    score = lb_match.iloc[0][col]
                    try:
                        result.at[idx, 'lb'] = float(score)
                        matches_found['lb'] += 1
                    except (ValueError, TypeError):
                        pass
                    break

print_step(f"Matches found - LMArena: {matches_found['lma']}, AA: {matches_found['aa']}, LiveBench: {matches_found['lb']}")

# Save the result
print_step("Saving data.csv...")
result.to_csv("data.csv", sep=";", index=False)
print_step(f"✓ Saved data.csv with {len(result)} models", "SUCCESS")

print("\n" + "=" * 80)
print_step("BUILD COMPLETED!", "SUCCESS")
print("=" * 80)
