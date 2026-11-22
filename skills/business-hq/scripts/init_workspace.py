#!/usr/bin/env python3
"""Create the shared business workspace that HQ and every department agent work in.

Never overwrites existing files, so it is safe to run again on a workspace that
already exists (it only fills in anything missing).

Usage:
    python3 init_workspace.py [path]          # default path: ./business
    python3 init_workspace.py --check [path]  # report what exists, change nothing
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

DEPARTMENTS = [
    ("00-hq", "HQ (main chat only)"),
    ("01-market", "biz-market-analyst"),
    ("02-competitors", "biz-competitor-analyst"),
    ("03-customers", "biz-customer-researcher"),
    ("04-strategy", "biz-strategist"),
    ("05-brand", "biz-brand-builder"),
    ("06-product", "biz-product-lead"),
    ("07-finance", "biz-finance-lead"),
    ("08-legal", "biz-legal-advisor"),
    ("09-marketing", "biz-marketing-lead"),
    ("10-content", "biz-content-lead"),
    ("11-sales", "biz-sales-lead"),
    ("12-commerce", "biz-commerce-lead"),
    ("13-retention", "biz-retention-lead"),
    ("14-operations", "biz-ops-lead"),
    ("15-fundraising", "biz-fundraising-lead"),
    ("16-review", "biz-red-team"),
]

HQ_FILES = [
    "BRIEF.md",
    "PROGRESS.md",
    "DECISIONS.md",
    "ASSUMPTIONS.md",
    "OPEN-QUESTIONS.md",
    "KEY-NUMBERS.md",
    "ACTUALS.csv",
]

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"


def build(root: Path) -> list[str]:
    today = dt.date.today().isoformat()
    actions: list[str] = []
    root.mkdir(parents=True, exist_ok=True)
    for folder, owner in DEPARTMENTS:
        d = root / folder
        if not d.exists():
            d.mkdir()
            actions.append(f"created {folder}/  (owner: {owner})")
    hq = root / "00-hq"
    for name in HQ_FILES:
        target = hq / name
        if target.exists():
            continue
        src = TEMPLATES / name
        if not src.exists():
            sys.exit(f"template missing: {src}")
        target.write_text(src.read_text(encoding="utf-8").replace("{{DATE}}", today), encoding="utf-8")
        actions.append(f"created 00-hq/{name}")
    readme = root / "README.md"
    if not readme.exists():
        lines = [
            "# Business workspace",
            "",
            "Created by the business-hq skill. HQ (the main chat) owns `00-hq/`.",
            "Each department agent writes only inside its own folder.",
            "",
            "| Folder | Owner |",
            "|--------|-------|",
        ]
        lines += [f"| `{f}/` | {o} |" for f, o in DEPARTMENTS]
        readme.write_text("\n".join(lines) + "\n", encoding="utf-8")
        actions.append("created README.md")
    return actions


def check(root: Path) -> int:
    if not root.exists():
        print(f"No workspace at {root}")
        return 1
    missing = [f for f, _ in DEPARTMENTS if not (root / f).is_dir()]
    missing += [f"00-hq/{n}" for n in HQ_FILES if not (root / "00-hq" / n).exists()]
    for folder, owner in DEPARTMENTS:
        d = root / folder
        files = sorted(p.name for p in d.glob("*")) if d.is_dir() else []
        print(f"{folder:16} {len(files):3d} files  {', '.join(files[:6])}{' ...' if len(files) > 6 else ''}")
    if missing:
        print("\nMissing: " + ", ".join(missing))
        return 2
    print("\nWorkspace complete.")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?", default="business")
    ap.add_argument("--check", action="store_true", help="report status without changing anything")
    args = ap.parse_args()
    root = Path(args.path).expanduser().resolve()
    if args.check:
        sys.exit(check(root))
    actions = build(root)
    print(f"Workspace: {root}")
    print("\n".join(actions) if actions else "Nothing to do, workspace already complete.")


if __name__ == "__main__":
    main()
