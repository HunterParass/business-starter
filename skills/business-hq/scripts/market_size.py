#!/usr/bin/env python3
"""Bottom-up market sizing (TAM / SAM / SOM) with a top-down cross-check.

Bottom-up means: count real customers you could name a category for, multiply by
what each is worth per year. Top-down (industry report figure x your slice) is
only used to sanity-check it. If the two disagree by more than 3x, one of them
is wrong and the report says so.

Input JSON:
{
  "currency": "CAD",
  "uncertainty_pct": 0.3,                 # optional, default 0.3 -> low/high range
  "segments": [
    {
      "name": "Independent cafes in Ontario",
      "customers": 6000,                  # how many potential customers exist
      "annual_value": 600,                # what one customer spends per year on this
      "serviceable_pct": 0.4,             # share you can actually serve (geo, language, fit)
      "obtainable_pct_year3": 0.03,       # share of serviceable you can win by year 3
      "source": "Statistics Canada business counts + 3 supplier quotes"
    }
  ],
  "top_down": {                           # optional
    "total_market_value": 50000000,
    "relevant_pct": 0.05,
    "source": "Industry report 2026"
  },
  "capacity_check": {                     # optional: can go-to-market deliver the SOM?
    "max_new_customers_per_month": 20,
    "months": 36
  }
}

Usage:
    python3 market_size.py sizing.json [--json]
"""
from __future__ import annotations

import argparse
import json
import sys


def fmt(x: float, cur: str) -> str:
    a = abs(x)
    if a >= 1e9:
        s = f"{x / 1e9:.2f}B"
    elif a >= 1e6:
        s = f"{x / 1e6:.2f}M"
    elif a >= 1e3:
        s = f"{x / 1e3:.1f}K"
    else:
        s = f"{x:.0f}"
    return f"{cur} {s}".strip()


def _num(seg: dict, key: str, lo: float, hi: float) -> float:
    v = seg.get(key)
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        raise ValueError(f"segment {seg.get('name', '?')!r}: {key} must be a number")
    if not lo <= v <= hi:
        raise ValueError(f"segment {seg.get('name', '?')!r}: {key}={v} outside {lo}..{hi}")
    return float(v)


def size(data: dict) -> dict:
    cur = data.get("currency", "")
    u = float(data.get("uncertainty_pct", 0.3))
    if not 0 <= u < 1:
        raise ValueError("uncertainty_pct must be between 0 and 1")
    segs = data.get("segments") or []
    if not segs:
        raise ValueError("at least one segment is required")

    rows = []
    tam = sam = som = som_customers = 0.0
    flags: list[str] = []
    for seg in segs:
        n = _num(seg, "customers", 0, 1e12)
        v = _num(seg, "annual_value", 0, 1e12)
        sp = _num(seg, "serviceable_pct", 0, 1)
        op = _num(seg, "obtainable_pct_year3", 0, 1)
        t, s, o = n * v, n * sp * v, n * sp * op * v
        oc = n * sp * op
        tam, sam, som, som_customers = tam + t, sam + s, som + o, som_customers + oc
        rows.append({"name": seg.get("name", ""), "tam": t, "sam": s, "som": o, "som_customers": oc,
                     "source": seg.get("source", "")})
        if not seg.get("source"):
            flags.append(f"{seg.get('name', 'segment')}: no source given, so treat these figures as assumptions")
        if op > 0.05:
            flags.append(
                f"{seg.get('name', 'segment')}: winning {op:.0%} of the serviceable market by year 3 is aggressive "
                "for a new entrant unless there is evidence (existing audience, partnerships, pre-orders)"
            )
        if sp > 0.6:
            flags.append(f"{seg.get('name', 'segment')}: serviceable share {sp:.0%} is high; justify why most of the market fits")

    result = {
        "currency": cur,
        "segments": rows,
        "tam": tam, "sam": sam, "som": som, "som_customers": som_customers,
        "range": {k: {"low": val * (1 - u), "high": val * (1 + u)} for k, val in (("tam", tam), ("sam", sam), ("som", som))},
        "uncertainty_pct": u,
        "flags": flags,
    }

    td = data.get("top_down")
    if td:
        total = float(td["total_market_value"])
        rel = float(td.get("relevant_pct", 1.0))
        td_value = total * rel
        ratio = (max(td_value, tam) / min(td_value, tam)) if min(td_value, tam) > 0 else float("inf")
        result["top_down"] = {"value": td_value, "source": td.get("source", ""), "ratio_vs_bottom_up_tam": ratio}
        if ratio > 3:
            flags.append(
                f"top-down ({fmt(td_value, cur)}) and bottom-up TAM ({fmt(tam, cur)}) differ by {ratio:.1f}x, "
                "so at least one set of assumptions is wrong; find out which before using either"
            )

    cap = data.get("capacity_check")
    if cap:
        reachable = float(cap["max_new_customers_per_month"]) * float(cap.get("months", 36))
        result["capacity_check"] = {"reachable_customers": reachable}
        if som_customers > reachable:
            flags.append(
                f"SOM needs about {som_customers:,.0f} customers but the go-to-market plan can win at most "
                f"{reachable:,.0f} in {cap.get('months', 36)} months; the SOM is capped by distribution, not demand"
            )
    return result


def to_markdown(r: dict) -> str:
    c = r["currency"]
    out = ["# Market size (bottom-up)", ""]
    out += ["| Layer | Base | Low | High |", "|---|---|---|---|"]
    for k, label in (("tam", "TAM (everyone who has the problem)"), ("sam", "SAM (who you can actually serve)"),
                     ("som", "SOM (what you can win by year 3)")):
        out.append(f"| {label} | {fmt(r[k], c)} | {fmt(r['range'][k]['low'], c)} | {fmt(r['range'][k]['high'], c)} |")
    out += ["", f"SOM implies roughly **{r['som_customers']:,.0f} customers** by year 3.", ""]
    out += ["| Segment | TAM | SAM | SOM | Source |", "|---|---|---|---|---|"]
    for s in r["segments"]:
        out.append(f"| {s['name']} | {fmt(s['tam'], c)} | {fmt(s['sam'], c)} | {fmt(s['som'], c)} | {s['source'] or 'ASSUMPTION'} |")
    if "top_down" in r:
        td = r["top_down"]
        out += ["", f"Top-down cross-check: {fmt(td['value'], c)} ({td['source'] or 'no source'}), "
                    f"{td['ratio_vs_bottom_up_tam']:.1f}x vs bottom-up TAM."]
    if r["flags"]:
        out += ["", "## Flags"] + [f"- {f}" for f in r["flags"]]
    out += ["", f"Range uses +/-{r['uncertainty_pct']:.0%} uncertainty. SOM is the number that matters for planning; "
                "TAM is mostly for pitch decks."]
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    with open(a.input, encoding="utf-8") as f:
        data = json.load(f)
    try:
        r = size(data)
    except (ValueError, KeyError) as e:
        sys.exit(f"error: {e}")
    print(json.dumps(r, indent=2) if a.json else to_markdown(r))


if __name__ == "__main__":
    main()
