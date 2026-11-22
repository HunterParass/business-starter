#!/usr/bin/env python3
"""Unit economics: what one customer is worth versus what it costs to win them.

Subscription example (price is per month):
    python3 unit_economics.py --model subscription --price 15 --gross-margin 0.8 \
        --churn 0.05 --cac 60 --currency CAD

Transactional example (price is per order):
    python3 unit_economics.py --model transactional --price 40 --gross-margin 0.45 \
        --orders-per-year 3 --lifetime-years 2 --marketing-spend 500 --new-customers 20

gross-margin is what's left of each payment after cost of goods, delivery and
payment fees (0.8 = 80%). CAC can be given directly or as marketing spend / new customers.
Add --json for machine-readable output.
"""
from __future__ import annotations

import argparse
import json
import sys


def compute(a: argparse.Namespace) -> dict:
    if not 0 < a.gross_margin <= 1:
        raise ValueError("--gross-margin must be between 0 and 1 (e.g. 0.6 for 60%)")
    if a.price <= 0:
        raise ValueError("--price must be positive")
    if a.cac is None:
        if a.marketing_spend is None or not a.new_customers:
            raise ValueError("give --cac, or both --marketing-spend and --new-customers")
        cac = a.marketing_spend / a.new_customers
    else:
        cac = a.cac
    if cac < 0:
        raise ValueError("CAC can't be negative")

    contrib_per_payment = a.price * a.gross_margin
    flags: list[str] = []
    res: dict = {"model": a.model, "currency": a.currency, "price": a.price,
                 "gross_margin": a.gross_margin, "cac": cac,
                 "contribution_per_payment": contrib_per_payment}

    if a.model == "subscription":
        if a.churn is None or not 0 < a.churn <= 1:
            raise ValueError("--churn (monthly, e.g. 0.05) is required for subscription")
        raw_life = 1 / a.churn
        life = min(raw_life, a.max_lifetime_months)
        if raw_life > a.max_lifetime_months:
            flags.append(f"lifetime capped at {a.max_lifetime_months} months (raw 1/churn = {raw_life:.0f}); "
                         "nobody should plan on customers staying longer than that")
        ltv = contrib_per_payment * life
        payback = cac / contrib_per_payment if contrib_per_payment > 0 else float("inf")
        res.update({"monthly_churn": a.churn, "expected_lifetime_months": life, "ltv": ltv,
                    "payback_months": payback})
        if a.churn > 0.10:
            flags.append(f"monthly churn {a.churn:.0%} means the average customer leaves in under 10 months; "
                         "retention is the first problem to fix")
        if payback > 12:
            flags.append(f"payback of {payback:.1f} months ties up cash for over a year per customer")
    else:
        if not a.orders_per_year or not a.lifetime_years:
            raise ValueError("--orders-per-year and --lifetime-years are required for transactional")
        orders = a.orders_per_year * a.lifetime_years
        ltv = contrib_per_payment * orders
        orders_to_payback = cac / contrib_per_payment if contrib_per_payment > 0 else float("inf")
        payback_months = orders_to_payback / (a.orders_per_year / 12)
        res.update({"orders_per_year": a.orders_per_year, "lifetime_years": a.lifetime_years,
                    "lifetime_orders": orders, "ltv": ltv, "orders_to_payback": orders_to_payback,
                    "payback_months": payback_months})
        if orders_to_payback > 1:
            flags.append(f"the first order doesn't cover CAC; you need {orders_to_payback:.1f} orders "
                         "to break even on each customer, so repeat purchase is critical")

    ratio = ltv / cac if cac > 0 else float("inf")
    res["ltv_to_cac"] = ratio
    if ratio < 1:
        flags.append("LTV is below CAC: every new customer loses money. Do not scale paid acquisition.")
    elif ratio < 3:
        flags.append(f"LTV:CAC of {ratio:.1f} is thin; 3+ is the usual target before spending heavily on growth")
    if a.gross_margin < 0.3:
        flags.append(f"gross margin {a.gross_margin:.0%} leaves little room for marketing, support and mistakes")
    if cac == 0:
        flags.append("CAC of 0 is never true; include your time, content costs or referral rewards")
    res["flags"] = flags
    return res


def to_markdown(r: dict) -> str:
    c = r["currency"]
    m = lambda x: f"{c} {x:,.2f}".strip()  # noqa: E731
    out = [f"# Unit economics ({r['model']})", "", "| Metric | Value |", "|---|---|"]
    out.append(f"| Price {'per month' if r['model'] == 'subscription' else 'per order'} | {m(r['price'])} |")
    out.append(f"| Gross margin | {r['gross_margin']:.0%} |")
    out.append(f"| Contribution per payment | {m(r['contribution_per_payment'])} |")
    if r["model"] == "subscription":
        out.append(f"| Monthly churn | {r['monthly_churn']:.1%} |")
        out.append(f"| Expected lifetime | {r['expected_lifetime_months']:.1f} months |")
    else:
        out.append(f"| Lifetime orders | {r['lifetime_orders']:.1f} |")
        out.append(f"| Orders to pay back CAC | {r['orders_to_payback']:.1f} |")
    out.append(f"| CAC | {m(r['cac'])} |")
    out.append(f"| LTV (gross-margin based) | {m(r['ltv'])} |")
    out.append(f"| LTV : CAC | {r['ltv_to_cac']:.1f} |")
    out.append(f"| Payback period | {r['payback_months']:.1f} months |")
    if r["flags"]:
        out += ["", "## Flags"] + [f"- {f}" for f in r["flags"]]
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", choices=["subscription", "transactional"], required=True)
    ap.add_argument("--price", type=float, required=True)
    ap.add_argument("--gross-margin", type=float, required=True)
    ap.add_argument("--churn", type=float, help="monthly churn, subscription only")
    ap.add_argument("--orders-per-year", type=float)
    ap.add_argument("--lifetime-years", type=float)
    ap.add_argument("--cac", type=float)
    ap.add_argument("--marketing-spend", type=float)
    ap.add_argument("--new-customers", type=float)
    ap.add_argument("--max-lifetime-months", type=float, default=60)
    ap.add_argument("--currency", default="")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        r = compute(a)
    except ValueError as e:
        sys.exit(f"error: {e}")
    print(json.dumps(r, indent=2) if a.json else to_markdown(r))


if __name__ == "__main__":
    main()
