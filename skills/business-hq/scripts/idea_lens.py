#!/usr/bin/env python3
"""Founder lens: rank business ideas on what matters to THIS founder.

Four measures, each 1-5:
  Idiot index      ease for this founder x money ceiling (after Hormozi's chart
                   of how hard a business is to run vs how much it can make)
  First quarter    realistic revenue in the first 3 months, simulated client by
                   client against the founder's real weekly hours
  Stickiness       how consistent the money is (recurring, low churn)
  AI compatibility share of the delivery work AI and automation can do

The lens score is the average of the four. It sits beside the go/pivot/kill
scorecard (scorecard.py), it doesn't replace it: an idea can be easy and sticky
and still have no paying customers.

Input: one or more JSON files shaped {"ideas": [ ... ]}, each idea with:
  id, name, founder_role, ease (1-5), money_ceiling (1-5), stickiness (1-5),
  ai_share (0-1), setup_price, monthly_price, sales_hours_per_client,
  setup_hours, monthly_hours, new_clients [m1, m2, m3], monthly_churn,
  local_competition (low/medium/high); optional: customer, problem, solution,
  evidence, flags.

First-quarter simulation: new clients pay the setup price in the month they
join and the monthly price from the next month. Each month, hours for existing
clients come first; new clients are capped by the hours left.

Usage:
    python3 idea_lens.py ideas1.json [ideas2.json ...] --hours 14 [--currency CAD] [--json]
    python3 idea_lens.py ... --same-ramp 1,1,2   # fairness check: give every idea the same
                                                  # first-quarter client ramp, so ideas scored by
                                                  # different agents are compared on price, hours,
                                                  # stickiness and AI share alone
"""
from __future__ import annotations

import argparse
import json
import sys

WEEKS_PER_MONTH = 52 / 12
Q1_BANDS = [(500, 1), (1500, 2), (3500, 3), (7000, 4)]  # revenue below the bound -> score; else 5
NUMERIC = {
    "ease": (1, 5), "money_ceiling": (1, 5), "stickiness": (1, 5), "ai_share": (0, 1),
    "setup_price": (0, None), "monthly_price": (0, None), "sales_hours_per_client": (0, None),
    "setup_hours": (0, None), "monthly_hours": (0, None), "monthly_churn": (0, 1),
}


def validate(idea: dict) -> None:
    w = f"idea {idea.get('id', '?')} ({idea.get('name', '')}): "
    for k, (lo, hi) in NUMERIC.items():
        v = idea.get(k)
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError(f"{w}{k} must be a number, got {v!r}")
        if v < lo or (hi is not None and v > hi):
            raise ValueError(f"{w}{k}={v} outside {lo}..{hi if hi is not None else 'inf'}")
    for k in ("ease", "money_ceiling", "stickiness"):
        if int(idea[k]) != idea[k]:
            raise ValueError(f"{w}{k} must be a whole number 1-5")
    nc = idea.get("new_clients")
    if not isinstance(nc, list) or len(nc) != 3 or not all(isinstance(x, (int, float)) and x >= 0 for x in nc):
        raise ValueError(f"{w}new_clients must be a list of 3 non-negative numbers")


def ai_score(share: float) -> int:
    return 1 if share < 0.2 else 2 if share < 0.4 else 3 if share < 0.6 else 4 if share < 0.8 else 5


def q1_score(revenue: float) -> int:
    for bound, score in Q1_BANDS:
        if revenue < bound:
            return score
    return 5


def quadrant(ease: int, money: int) -> str:
    easy, big = ease >= 4, money >= 4
    if easy and big:
        return "Sweet spot (easy and big)"
    if easy:
        return "Starter cash (easy, capped)"
    if big:
        return "Hard but big"
    if ease <= 2 or money <= 2:
        return "Avoid (hard and capped)"
    return "Middle (moderate on both)"


def simulate_q1(idea: dict, hours_per_week: float) -> dict:
    available = hours_per_week * WEEKS_PER_MONTH
    per_new = idea["sales_hours_per_client"] + idea["setup_hours"]
    paying = 0.0
    months, capped = [], False
    for m, planned in enumerate(idea["new_clients"], 1):
        existing_hours = paying * idea["monthly_hours"]
        room = max(0.0, available - existing_hours)
        new = min(planned, room / per_new) if per_new > 0 else planned
        if new < planned - 1e-9:
            capped = True
        recurring = paying * idea["monthly_price"]
        revenue = new * idea["setup_price"] + recurring
        hours = new * per_new + existing_hours
        months.append({"month": m, "new_clients": new, "paying_clients": paying, "revenue": revenue,
                       "recurring_revenue": recurring, "hours": hours, "hours_available": available})
        paying = paying * (1 - idea["monthly_churn"]) + new
    rev = sum(x["revenue"] for x in months)
    hrs = sum(x["hours"] for x in months)
    m3 = months[-1]
    return {
        "months": months, "q1_revenue": rev, "q1_new_clients": sum(x["new_clients"] for x in months),
        "q1_hours": hrs, "effective_hourly": rev / hrs if hrs else 0.0,
        "mrr_after_q1": paying * idea["monthly_price"], "clients_after_q1": paying,
        "recurring_share_month3": (m3["recurring_revenue"] / m3["revenue"]) if m3["revenue"] else 0.0,
        "capped_by_hours": capped,
    }


def evaluate(ideas: list[dict], hours_per_week: float) -> list[dict]:
    out = []
    for idea in ideas:
        validate(idea)
        q = simulate_q1(idea, hours_per_week)
        idiot = (idea["ease"] + idea["money_ceiling"]) / 2
        scores = {"idiot_index": idiot, "first_quarter": q1_score(q["q1_revenue"]),
                  "stickiness": idea["stickiness"], "ai_compatibility": ai_score(idea["ai_share"])}
        flags = []
        if q["capped_by_hours"]:
            flags.append("the founder's hours cap how many clients can be taken on in the first quarter")
        if idea["stickiness"] >= 4 and idea["monthly_price"] == 0:
            flags.append("scored sticky but has no monthly price; check the stickiness score")
        if idea["ai_share"] >= 0.8 and idea.get("local_competition") == "high":
            flags.append("AI does most of the work and local competition is high: others (and the client) can copy it, "
                         "so the moat has to be trust, niche or relationships")
        if q["q1_hours"] > 0 and q["effective_hourly"] < 20:
            flags.append(f"first-quarter earnings are about {q['effective_hourly']:.0f}/h, below what a part-time job pays")
        if sum(idea["new_clients"]) == 0:
            flags.append("no new clients assumed in the first quarter")
        if idea.get("flags"):
            flags.append(str(idea["flags"]))
        out.append({
            "id": idea.get("id", ""), "name": idea.get("name", ""), "founder_role": idea.get("founder_role", ""),
            "customer": idea.get("customer", ""), "local_competition": idea.get("local_competition", ""),
            "ease": idea["ease"], "money_ceiling": idea["money_ceiling"],
            "quadrant": quadrant(idea["ease"], idea["money_ceiling"]), "ai_share": idea["ai_share"],
            "scores": scores, "lens_score": round(sum(scores.values()) / 4, 2), "q1": q, "flags": flags,
        })
    out.sort(key=lambda r: (-r["lens_score"], -r["q1"]["q1_revenue"]))
    return out


def to_md(rows: list[dict], cur: str, hours: float) -> str:
    m = lambda x: f"{cur} {x:,.0f}".strip()  # noqa: E731
    out = ["# Founder lens ranking", "",
           f"Founder time: {hours:g} h/week (about {hours * WEEKS_PER_MONTH:.0f} h/month). Each measure is 1-5; "
           "the lens score is their average.", "",
           "| # | Idea | **Lens** | Idiot index (ease / money) | First quarter: revenue, clients | Monthly income after Q1 | Stickiness | AI compatibility | Local competition |",
           "|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        q, s = r["q1"], r["scores"]
        out.append(
            f"| {i} | **{r['id']}** {r['name']} | **{r['lens_score']:.2f}** | {s['idiot_index']:.1f} ({r['ease']}/{r['money_ceiling']}, "
            f"{r['quadrant']}) | {s['first_quarter']}: {m(q['q1_revenue'])}, {q['q1_new_clients']:.1f} clients | "
            f"{m(q['mrr_after_q1'])} | {s['stickiness']} | {s['ai_compatibility']} ({r['ai_share']:.0%} of the work) | "
            f"{r['local_competition']} |")
    out += ["", "## Detail", ""]
    for r in rows:
        q = r["q1"]
        out.append(f"### {r['id']}: {r['name']}")
        if r["customer"]:
            out.append(f"- Customer: {r['customer']}")
        if r["founder_role"]:
            out.append(f"- What the founder still does: {r['founder_role']}")
        out.append(f"- First quarter: {m(q['q1_revenue'])} from {q['q1_new_clients']:.1f} new clients in "
                   f"{q['q1_hours']:.0f} hours (about {m(q['effective_hourly'])}/h); "
                   f"{q['clients_after_q1']:.1f} paying monthly after Q1 = {m(q['mrr_after_q1'])}/month.")
        out.append("- By month: " + "; ".join(
            f"M{x['month']} {x['new_clients']:.1f} new, {m(x['revenue'])}, {x['hours']:.0f} h" for x in q["months"]))
        for f in r["flags"]:
            out.append(f"- Flag: {f}")
        out.append("")
    out += ["Bands: first-quarter revenue under 500 = 1, under 1,500 = 2, under 3,500 = 3, under 7,000 = 4, else 5. "
            "AI compatibility: under 20% of the work = 1, under 40% = 2, under 60% = 3, under 80% = 4, else 5. "
            "Idiot index quadrant: ease 4+ is easy, money 4+ is big; a 2 or lower on either (without the other "
            "being 4+) is 'avoid'.",
            "", "A high lens score doesn't mean customers will pay; check scorecard.py and real deposits."]
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--hours", type=float, default=14, help="founder hours per week (default 14)")
    ap.add_argument("--currency", default="")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--same-ramp", help="override every idea's new_clients, e.g. 1,1,2")
    a = ap.parse_args()
    ideas = []
    try:
        for path in a.inputs:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            ideas += data["ideas"] if isinstance(data, dict) else data
        if a.hours <= 0:
            raise ValueError("--hours must be positive")
        if a.same_ramp:
            ramp = [float(x) for x in a.same_ramp.split(",")]
            if len(ramp) != 3 or any(x < 0 for x in ramp):
                raise ValueError("--same-ramp needs three non-negative numbers, e.g. 1,1,2")
            for idea in ideas:
                idea["new_clients"] = ramp
        rows = evaluate(ideas, a.hours)
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as e:
        sys.exit(f"error: {e}")
    md = to_md(rows, a.currency, a.hours)
    if a.same_ramp:
        md = md.replace("# Founder lens ranking", f"# Founder lens ranking (same ramp {a.same_ramp} for every idea)", 1)
    print(json.dumps(rows, indent=2) if a.json else md)


if __name__ == "__main__":
    main()
