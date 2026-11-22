#!/usr/bin/env python3
"""Go / Pivot / Kill scorecard for a business idea.

The model (or the founder) scores each dimension 1-5 and tags how strong the
evidence is. This script does the weighting and applies the verdict rules, so
the verdict can't drift with the mood of the conversation.

Input JSON:
{
  "idea": "Meal-prep subscription for night-shift nurses",
  "scores": {
    "problem_severity":      {"score": 4, "evidence": "medium", "note": "..."},
    "willingness_to_pay":    {"score": 3, "evidence": "weak",   "note": "..."},
    ... one entry for every dimension in DIMENSIONS ...
  }
}
evidence: "strong" (paying customers, pre-orders, LOIs, 10+ interviews)
          "medium" (sourced desk research, a few conversations)
          "weak"   (opinion, founder belief, no source)

Usage:
    python3 scorecard.py scores.json            # markdown report
    python3 scorecard.py scores.json --json     # machine-readable
    python3 scorecard.py --template             # print a blank input file
"""
from __future__ import annotations

import argparse
import json
import sys

# name: (weight, critical, question)
DIMENSIONS: dict[str, tuple[float, bool, str]] = {
    "problem_severity": (0.15, True, "How painful, frequent and urgent is the problem for the first segment?"),
    "willingness_to_pay": (0.15, True, "Is there evidence this segment pays (or would pay) enough to matter?"),
    "distribution_access": (0.15, True, "Can the founder reach the first 100 customers cheaply and repeatably?"),
    "market_size": (0.10, False, "Is the serviceable market big enough for the founder's goal?"),
    "competition_and_wedge": (0.10, False, "Is there a clear wedge versus what customers use today?"),
    "founder_fit": (0.10, False, "Do the founder's skills, access and time fit this business?"),
    "feasibility": (0.10, False, "Can a first version be built with the budget, skills and time available?"),
    "unit_economics": (0.10, False, "Can each customer plausibly be worth more than it costs to win and serve?"),
    "risk_and_regulation": (0.05, False, "Are legal, safety and platform risks manageable? (5 = low risk)"),
}
EVIDENCE = {"strong", "medium", "weak"}

BUILD_MIN = 3.4
KILL_BELOW = 2.6
WEAK_SHARE_CAP = 0.5


def evaluate(data: dict) -> dict:
    scores = data.get("scores") or {}
    missing = [d for d in DIMENSIONS if d not in scores]
    unknown = [d for d in scores if d not in DIMENSIONS]
    if missing or unknown:
        msg = []
        if missing:
            msg.append("missing dimensions: " + ", ".join(missing))
        if unknown:
            msg.append("unknown dimensions: " + ", ".join(unknown))
        raise ValueError("; ".join(msg))

    rows = []
    total = 0.0
    weak_weight = 0.0
    for name, (weight, critical, question) in DIMENSIONS.items():
        entry = scores[name]
        s = entry.get("score")
        if not isinstance(s, int) or not 1 <= s <= 5:
            raise ValueError(f"{name}: score must be an integer 1-5, got {s!r}")
        ev = str(entry.get("evidence", "weak")).lower()
        if ev not in EVIDENCE:
            raise ValueError(f"{name}: evidence must be one of {sorted(EVIDENCE)}, got {ev!r}")
        total += weight * s
        if ev == "weak":
            weak_weight += weight
        rows.append({
            "dimension": name, "weight": weight, "critical": critical, "score": s,
            "evidence": ev, "note": entry.get("note", ""), "question": question,
        })

    weighted = round(total, 2)
    crit = [r for r in rows if r["critical"]]
    crit_min = min(r["score"] for r in crit)

    reasons = []
    if weighted < KILL_BELOW or crit_min == 1:
        verdict = "KILL"
        if crit_min == 1:
            reasons.append("a critical dimension scored 1, which no strength elsewhere can make up for")
        if weighted < KILL_BELOW:
            reasons.append(f"weighted score {weighted} is below {KILL_BELOW}")
    elif weighted < BUILD_MIN or crit_min <= 2:
        verdict = "PIVOT"
        if crit_min <= 2:
            reasons.append("a critical dimension scored 2 or less, so fix that before building")
        if weighted < BUILD_MIN:
            reasons.append(f"weighted score {weighted} is below the build threshold of {BUILD_MIN}")
    else:
        verdict = "BUILD"
        reasons.append(f"weighted score {weighted} clears {BUILD_MIN} and no critical dimension scores 2 or less")

    weak_critical = [r["dimension"] for r in crit if r["evidence"] == "weak"]
    if verdict == "BUILD" and (weak_weight > WEAK_SHARE_CAP or weak_critical):
        verdict = "TEST FIRST"
        if weak_critical:
            reasons.append(
                "promising, but " + ", ".join(weak_critical) + " rests on weak evidence; prove it cheaply before building"
            )
        if weak_weight > WEAK_SHARE_CAP:
            reasons.append(
                f"{round(weak_weight * 100)}% of the score rests on weak evidence, so it is promising but unproven"
            )

    # Biggest risk: lowest score, critical dimensions first, then by weight.
    ranked = sorted(rows, key=lambda r: (r["score"], not r["critical"], -r["weight"]))
    biggest = ranked[0]
    unproven = [r["dimension"] for r in rows if r["evidence"] == "weak" and r["critical"]]

    return {
        "idea": data.get("idea", ""),
        "weighted_score": weighted,
        "verdict": verdict,
        "reasons": reasons,
        "weak_evidence_share": round(weak_weight, 2),
        "biggest_risk": biggest["dimension"],
        "unproven_critical": unproven,
        "rows": rows,
    }


def to_markdown(res: dict) -> str:
    out = [f"# Go / Pivot / Kill scorecard: {res['idea'] or 'unnamed idea'}", ""]
    out.append(f"**Verdict: {res['verdict']}** (weighted score {res['weighted_score']} / 5)")
    out.append("")
    for r in res["reasons"]:
        out.append(f"- {r}")
    out += ["", "| Dimension | Weight | Critical | Score | Evidence | Note |", "|---|---|---|---|---|---|"]
    for r in res["rows"]:
        out.append(
            f"| {r['dimension']} | {int(r['weight'] * 100)}% | {'yes' if r['critical'] else ''} | "
            f"{r['score']} | {r['evidence']} | {r['note']} |"
        )
    out += ["", f"**Biggest risk:** {res['biggest_risk']}"]
    if res["unproven_critical"]:
        out.append("**Critical but unproven (test these first):** " + ", ".join(res["unproven_critical"]))
    out.append(f"**Share of score resting on weak evidence:** {round(res['weak_evidence_share'] * 100)}%")
    out += [
        "",
        "Verdict rules: KILL if weighted < 2.6 or any critical dimension = 1. "
        "PIVOT if weighted < 3.4 or any critical dimension <= 2. Otherwise BUILD, "
        "downgraded to TEST FIRST when a critical dimension rests on weak evidence or more than "
        "half the weight does.",
    ]
    return "\n".join(out)


def template() -> dict:
    return {
        "idea": "",
        "scores": {d: {"score": 3, "evidence": "weak", "note": q} for d, (_, _, q) in DIMENSIONS.items()},
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", nargs="?")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--template", action="store_true")
    a = ap.parse_args()
    if a.template:
        print(json.dumps(template(), indent=2))
        return
    if not a.input:
        ap.error("input file required (or --template)")
    with open(a.input, encoding="utf-8") as f:
        data = json.load(f)
    try:
        res = evaluate(data)
    except ValueError as e:
        sys.exit(f"error: {e}")
    print(json.dumps(res, indent=2) if a.json else to_markdown(res))


if __name__ == "__main__":
    main()
