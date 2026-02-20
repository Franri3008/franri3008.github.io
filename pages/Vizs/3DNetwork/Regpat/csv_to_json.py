import argparse
import csv
import json
from pathlib import Path;

def cast_value(v, enable_infer):
    if not enable_infer:
        return v;
    s = v.strip();
    if s == "":
        return None;
    low = s.lower();
    if low == "true":
        return True;
    if low == "false":
        return False;
    try:
        i = int(s);
        return i;
    except ValueError:
        pass;
    try:
        f = float(s);
        return f;
    except ValueError:
        pass;
    return s;

parser = argparse.ArgumentParser();
parser.add_argument("input_csv", type=Path);
parser.add_argument("output_json", type=Path);
parser.add_argument("--indent", type=int, default=2);
parser.add_argument("--encoding", default="utf-8");
parser.add_argument("--infer", action="store_true");
args = parser.parse_args();

with args.input_csv.open("r", encoding=args.encoding, newline="") as f_in:
    reader = csv.DictReader(f_in);
    rows = [];
    for row in reader:
        rows.append({k: cast_value(v, args.infer) for k, v in row.items()});

args.output_json.parent.mkdir(parents=True, exist_ok=True);
with args.output_json.open("w", encoding=args.encoding) as f_out:
    json.dump(rows, f_out, ensure_ascii=False, indent=args.indent);