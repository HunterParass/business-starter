#!/usr/bin/env python3
"""Compare real monthly results with the plan from financial_model.py.

Once the business is running, the founder logs real numbers each month in
00-hq/ACTUALS.csv. This script lines them up against the base-case plan
(07-finance/monthly.csv) and flags where reality is drifting.

ACTUALS.csv columns (only `month` is required, fill what you know):
    month,revenue,operating_expenses,net_profit,ending_cash,new_customers,notes
`month` is the model month number (1 = first month of the plan).

Usage:
    python3 plan_vs_actual.py business/07-finance/monthly.csv business/00-hq/ACTUALS.csv
    python3 plan_vs_actual.py --template          # print an empty ACTUALS.csv
Options:
    --threshold 0.2   flag differences bigger than 20% (default)
    --json
"""
from __future__ import annotations

import argparse
import csv
import json
import sys

METRICS = {
    # actuals column: (plan line, higher_is_better)
    "revenue": ("Total revenue", True),
    "operating_expenses": ("Total operating expenses", False),
    "net_profit": ("Net profit", True),
    "ending_cash": ("Ending cash", True),
    "new_customers": ("__new_customers__", True),
}
TEMPLATE = "month,revenue,operating_expenses,net_profit,ending_cash,new_customers,notes\n"


def load_plan(path: str) -> dict[str, list[float]]:
    with open(path, encoding="utf-8") as f:
        rows = list(csv.reader(f))
    if not rows or rows[0][0] != "Line":
        raise ValueError(f"{path} doesn't look like financial_model.py monthly.csv output")
    plan = {r[0]: [float(x) for x in r[1:]] for r in rows[1:] if r}
    new = [k for k in plan if k.endswith(": new customers")]
    if new:
        n = len(next(iter(plan.values())))
        plan["__new_customers__"] = [sum(plan[k][i] for k in new) for i in range(n)]
    return plan


def load_actuals(path: str) -> list[dict]:
    out = []
    with open(path, encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f), 2):
            if not row.get("month", "").strip():
                continue
            try:
                m = int(float(row["month"]))
            except ValueError:
                raise ValueError(f"line {i}: month must be a number, got {row['month']!r}")
            rec = {"month": m, "notes": (row.get("notes") or "").strip()}
            for k in METRICS:
                v = (row.get(k) or "").strip().replace(",", "")
                if v:
                    try:
                        rec[k] = float(v)
                    except ValueError:
                        raise ValueError(f"line {i}: {k} must be a number, got {v!r}")
            out.append(rec)
    if not out:
        raise ValueError("no rows with a month number in the actuals file")
    return sorted(out, key=lambda r: r["month"])


def compare(plan: dict, actuals: list[dict], threshold: float) -> dict:
    n = len(next(iter(plan.values())))
    rows, flags = [], []
    streak = {k: 0 for k in METRICS}
    worst_streak = {k: 0 for k in METRICS}
    for a in actuals:
        m = a["month"]
        if not 1 <= m <= n:
            flags.append(f"month {m} is outside the plan's {n} months; skipped")
            continue
        for k, (line, up_good) in METRICS.items():
            if k not in a or line not in plan:
                continue
            p, v = plan[line][m - 1], a[k]
            diff = v - p
            pct = diff / abs(p) if p else None
            bad = pct is not None and abs(pct) > threshold and ((pct < 0) if up_good else (pct > 0))
            streak[k] = streak[k] + 1 if bad else 0
            worst_streak[k] = max(worst_streak[k], streak[k])
            rows.append({"month": m, "metric": k, "plan": p, "actual": v, "diff": diff, "diff_pct": pct, "off_track": bad})
    for k, s in worst_streak.items():
        if s >= 2:
            flags.append(f"{k.replace('_', ' ')} has been off plan in the bad direction for {s} months in a row: "
                         "update the assumptions and rerun the financial model rather than hoping it corrects")
    totals = {}
    for k in ("revenue", "operating_expenses", "new_customers"):
        got = [r for r in rows if r["metric"] == k]
        if got:
            totals[k] = {"plan": sum(r["plan"] for r in got), "actual": sum(r["actual"] for r in got)}
    last_cash = [r for r in rows if r["metric"] == "ending_cash"]
    if last_cash and last_cash[-1]["actual"] < 0:
        flags.append("ending cash is negative: this needs action now (cut costs, collect receivables, pre-sell)")
    return {"threshold": threshold, "rows": rows, "totals": totals, "flags": flags}


def to_md(r: dict) -> str:
    out = ["# Plan vs actual", "", f"Off-track means more than {r['threshold']:.0%} worse than plan.", "",
           "| Month | Metric | Plan | Actual | Difference | Status |", "|---|---|---|---|---|---|"]
    for x in r["rows"]:
        pct = f" ({x['diff_pct']:+.0%})" if x["diff_pct"] is not None else ""
        out.append(f"| {x['month']} | {x['metric'].replace('_', ' ')} | {x['plan']:,.0f} | {x['actual']:,.0f} | "
                   f"{x['diff']:+,.0f}{pct} | {'OFF TRACK' if x['off_track'] else 'ok'} |")
    if r["totals"]:
        out += ["", "## To date", "", "| Metric | Plan | Actual | Difference |", "|---|---|---|---|"]
        for k, t in r["totals"].items():
            out.append(f"| {k.replace('_', ' ')} | {t['plan']:,.0f} | {t['actual']:,.0f} | {t['actual'] - t['plan']:+,.0f} |")
    if r["flags"]:
        out += ["", "## Flags"] + [f"- {f}" for f in r["flags"]]
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan", nargs="?")
    ap.add_argument("actuals", nargs="?")
    ap.add_argument("--threshold", type=float, default=0.2)
    ap.add_argument("--template", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.template:
        print(TEMPLATE, end="")
        return
    if not (a.plan and a.actuals):
        ap.error("give the plan monthly.csv and the ACTUALS.csv paths (or --template)")
    try:
        r = compare(load_plan(a.plan), load_actuals(a.actuals), a.threshold)
    except (ValueError, OSError) as e:
        sys.exit(f"error: {e}")
    print(json.dumps(r, indent=2) if a.json else to_md(r))


if __name__ == "__main__":
    main()
