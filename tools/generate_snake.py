#!/usr/bin/env python3
"""
generate_snake.py

Simple script to create dated empty commits following a pattern file
(`snake_pattern.txt`) so the GitHub contribution graph shows a custom
pattern (a "snake").

Usage (in GitHub Actions): set secrets `SNAKE_NAME`, `SNAKE_EMAIL`, and
optionally `SNAKE_START_DATE` (YYYY-MM-DD). The workflow checks out the
repo, runs this script, and pushes the commits.

WARNING: Commits will be created in this repository's branch. Set the
name/email to an email associated with your GitHub account if you want
contributions to count on your profile.
"""

import os
import subprocess
from datetime import datetime, timedelta

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PATTERN_FILE = os.path.join(ROOT, "snake_pattern.txt")


def load_pattern(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    # each line is a week (column) with 7 chars 0/1 for Sun..Sat
    return lines


def date_for_cell(start_date, week_index, day_index):
    # start_date is the Sunday of the first week
    return start_date + timedelta(weeks=week_index, days=day_index)


def ensure_git_config(name, email):
    subprocess.run(["git", "config", "user.name", name], check=True)
    subprocess.run(["git", "config", "user.email", email], check=True)


def make_commit_on(date, message):
    iso = date.strftime("%Y-%m-%dT12:00:00")
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = iso
    env["GIT_COMMITTER_DATE"] = iso
    # Make an empty commit so the tree doesn't change
    subprocess.run(["git", "commit", "--allow-empty", "-m", message], check=True, env=env)


def main():
    pattern = load_pattern(PATTERN_FILE)
    if not pattern:
        print("No pattern found in", PATTERN_FILE)
        return

    # Determine start date: either user-provided START_DATE or 52 weeks back Sunday
    start_date_str = os.environ.get("START_DATE")
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        # normalize to Sunday
        start_date -= timedelta(days=start_date.weekday() + 1) if start_date.weekday() != 6 else timedelta(0)
    else:
        today = datetime.utcnow().date()
        # go back number of weeks equal to pattern length
        weeks = len(pattern)
        start_date = datetime.combine(today - timedelta(weeks=weeks), datetime.min.time())
        # shift to nearest previous Sunday
        start_date -= timedelta(days=start_date.weekday() + 1) if start_date.weekday() != 6 else timedelta(0)

    name = os.environ.get("SNAKE_NAME") or os.environ.get("GITHUB_ACTOR") or "github-actions"
    email = os.environ.get("SNAKE_EMAIL") or f"{os.environ.get('GITHUB_ACTOR','actions')}@users.noreply.github.com"

    ensure_git_config(name, email)

    # Iterate weeks (columns) left-to-right; pattern lines are columns
    for week_idx, col in enumerate(pattern):
        # Expect 7 characters (Sun..Sat). If shorter, pad with 0s
        col = col.ljust(7, "0")[:7]
        for day_idx, ch in enumerate(col):
            if ch == "1":
                dt = date_for_cell(start_date, week_idx, day_idx)
                msg = f"contrib: snake {week_idx}-{day_idx} ({dt.date()})"
                print("Creating commit for", dt.date())
                make_commit_on(dt, msg)

    print("All commits created.")


if __name__ == "__main__":
    main()
