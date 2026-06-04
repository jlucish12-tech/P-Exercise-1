import argparse
import json
import re
import csv
from datetime import datetime
from collections import Counter


PLAIN_RE = re.compile(
    r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(\w+)\s+(.*)'
)


def parse_line(line):
    try:
        d = json.loads(line)
        return d['timestamp'], d['level'].upper(), d['message']
    except (json.JSONDecodeError, KeyError):
        pass

    m = PLAIN_RE.match(line)
    if m:
        return m.group(1), m.group(2).upper(), m.group(3)

    return None  


def read_log_file(filepath):
    
    with open(filepath, 'r') as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if line:
                print(f"Line {i}: {line}")


def analyze(filepath, level_filter=None, from_dt=None, to_dt=None, export_path=None):

    fmt = '%Y-%m-%d %H:%M:%S'
    dt_from = datetime.strptime(from_dt, fmt) if from_dt else None
    dt_to   = datetime.strptime(to_dt,   fmt) if to_dt   else None

    errors = warnings = info = total = 0
    error_msgs = Counter()
    fail_times = []

    with open(filepath) as f:
        for line in f:
            parsed = parse_line(line.strip())
            if not parsed:
                continue 

            ts, level, msg = parsed

            
            dt = datetime.strptime(ts, fmt)

            
            if level_filter and level != level_filter.upper():
                continue
            if dt_from and dt < dt_from:
                continue
            if dt_to and dt > dt_to:
                continue

            
            total += 1
            if level == 'ERROR':
                errors += 1
                error_msgs[msg] += 1
                fail_times.append(ts.split()[1])   
            elif level == 'WARNING':
                warnings += 1
            elif level == 'INFO':
                info += 1

   
    mc = error_msgs.most_common(1)[0][0] if error_msgs else 'none'

   
    print(f"Total logs:          {total}")
    print(f"Errors:              {errors}")
    print(f"Warnings:            {warnings}")
    print(f"Info:                {info}")
    print(f"Most frequent error: {mc!r}")
    print(f"Failure timestamps:  {', '.join(fail_times) or 'none'}")

    
    if export_path:
        with open(export_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['metric', 'value'])
            writer.writerows([
                ['total_logs',        total],
                ['errors',            errors],
                ['warnings',          warnings],
                ['info',              info],
                ['most_common_error', mc],
            ])
        print(f"\n✓ Exported to {export_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Log analyser')
    parser.add_argument('--file',   required=True,  help='Path to log file')
    parser.add_argument('--level',  default=None,   help='Filter by level: ERROR, WARNING, INFO')
    parser.add_argument('--from',   dest='from_dt', default=None, help='Start time  "YYYY-MM-DD HH:MM:SS"')
    parser.add_argument('--to',     dest='to_dt',   default=None, help='End time    "YYYY-MM-DD HH:MM:SS"')
    parser.add_argument('--export', default=None,   help='Export summary to CSV, e.g. summary.csv')
    parser.add_argument('--preview', action='store_true', help='Print raw lines with line numbers before analysis')

    args = parser.parse_args()

    if args.preview:
        print("=== FILE PREVIEW ===")
        read_log_file(args.file)
        print("=== ANALYSIS ===")

    analyze(args.file, args.level, args.from_dt, args.to_dt, args.export)
