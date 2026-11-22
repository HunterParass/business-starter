#!/usr/bin/env python3
"""Pricing calculator for product and service businesses.

PRODUCT mode compares what you actually keep per order on every sales channel
(your own site, marketplaces, social shops, wholesale, markets) after product
cost, platform and payment fees, shipping, returns and ad cost. It also gives
the break-even ROAS, the most you can pay to win an order, and the price you'd
need to hit a target margin.

    python3 pricing_calc.py product channels.json
    python3 pricing_calc.py product --template       # example input

Platform and payment fees change often and differ by country. Look up the
current numbers on each platform's own fee page and date them; the template's
fee values are placeholders, not facts.

SERVICE mode works out the hourly, day and package rate you need to hit a
target income, given realistic billable hours and overhead.

    python3 pricing_calc.py service --target-income 40000 --overhead 3000 \
        --billable-hours 20 --weeks 46 --market-rate 45 --currency CAD

Add --json to either mode for machine-readable output.
"""
from __future__ import annotations

import argparse
import json
import sys

PRODUCT_TEMPLATE = {
    "currency": "CAD",
    "product": "Hand-poured soy candle, 8 oz",
    "unit_costs": {"materials": 4.10, "packaging": 0.90, "labour": 1.50, "inbound_shipping": 0.40},
    "duties_pct": 0.0,
    "target_margin_pct": 0.25,
    "channels": [
        {"name": "Own website", "price": 28, "units_per_order": 1.6, "platform_fee_pct": 0.0,
         "payment_fee_pct": 0.029, "payment_fee_fixed": 0.30, "fulfilment_per_order": 1.50,
         "shipping_cost": 11.00, "shipping_charged": 6.00, "returns_pct": 0.03, "ad_cost_per_order": 9.00,
         "fee_source": "PLACEHOLDER: check the platform's current pricing page"},
        {"name": "Handmade marketplace", "price": 30, "units_per_order": 1.3, "platform_fee_pct": 0.095,
         "payment_fee_pct": 0.03, "payment_fee_fixed": 0.25, "fixed_fee_per_order": 0.27,
         "fulfilment_per_order": 1.50, "shipping_cost": 11.00, "shipping_charged": 8.00, "returns_pct": 0.03,
         "ad_cost_per_order": 4.00, "fee_source": "PLACEHOLDER: check the marketplace's current fee page"},
        {"name": "Weekend craft market", "price": 26, "units_per_order": 1.4, "platform_fee_pct": 0.0,
         "payment_fee_pct": 0.027, "payment_fee_fixed": 0.0, "fulfilment_per_order": 0.0,
         "shipping_cost": 0.0, "shipping_charged": 0.0, "returns_pct": 0.0, "ad_cost_per_order": 3.50,
         "fee_source": "booth fee spread per order as ad_cost_per_order"},
        {"name": "Wholesale to local shops", "price": 14, "units_per_order": 24, "platform_fee_pct": 0.0,
         "payment_fee_pct": 0.0, "payment_fee_fixed": 0.0, "fulfilment_per_order": 3.00,
         "shipping_cost": 18.00, "shipping_charged": 0.0, "returns_pct": 0.0, "ad_cost_per_order": 0.0,
         "fee_source": "no platform"},
    ],
}

CHANNEL_KEYS = {
    "price": (0, None), "units_per_order": (0.0001, None), "platform_fee_pct": (0, 1), "payment_fee_pct": (0, 1),
    "payment_fee_fixed": (0, None), "fixed_fee_per_order": (0, None), "fulfilment_per_order": (0, None),
    "shipping_cost": (0, None), "shipping_charged": (0, None), "returns_pct": (0, 1), "ad_cost_per_order": (0, None),
}


def _num(d: dict, k: str, default: float, lo, hi, where: str) -> float:
    v = d.get(k, default)
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"{where}{k} must be a number")
    if lo is not None and v < lo or hi is not None and v > hi:
        raise ValueError(f"{where}{k}={v} out of range")
    return float(v)


def product(data: dict) -> dict:
    costs = data.get("unit_costs") or {}
    if not costs:
        raise ValueError("unit_costs is required (materials, packaging, labour, inbound_shipping...)")
    base_unit = sum(_num(costs, k, 0, 0, None, "unit_costs.") for k in costs)
    duties = _num(data, "duties_pct", 0, 0, 1, "")
    landed = base_unit * (1 + duties)
    target = _num(data, "target_margin_pct", 0.25, 0, 0.95, "")
    channels = data.get("channels") or []
    if not channels:
        raise ValueError("at least one channel is required")

    rows = []
    for ch in channels:
        w = f"channel {ch.get('name', '?')!r}: "
        c = {k: _num(ch, k, 0 if k not in ("units_per_order",) else 1, lo, hi, w) for k, (lo, hi) in CHANNEL_KEYS.items()}
        if c["price"] <= 0:
            raise ValueError(f"{w}price must be positive")
        u = c["units_per_order"]
        revenue = c["price"] * u + c["shipping_charged"]
        pct_costs = revenue * (c["platform_fee_pct"] + c["payment_fee_pct"] + c["returns_pct"])
        fixed = (c["payment_fee_fixed"] + c["fixed_fee_per_order"] + landed * u + c["fulfilment_per_order"]
                 + c["shipping_cost"])
        before_ads = revenue - pct_costs - fixed
        after_ads = before_ads - c["ad_cost_per_order"]
        variable = c["platform_fee_pct"] + c["payment_fee_pct"] + c["returns_pct"]
        denom = 1 - variable - target
        need_rev = (fixed + c["ad_cost_per_order"]) / denom if denom > 0 else float("inf")
        need_price = (need_rev - c["shipping_charged"]) / u if denom > 0 else float("inf")
        flags = []
        if after_ads < 0:
            flags.append("loses money on every order after ad cost")
        elif revenue > 0 and after_ads / revenue < target:
            flags.append(f"margin below the {target:.0%} target; raise price to about {need_price:,.2f} or cut costs")
        if before_ads <= 0:
            flags.append("loses money even with zero ad spend")
        if c["shipping_cost"] - c["shipping_charged"] > 0.25 * revenue and c["shipping_cost"] > 0:
            flags.append("shipping subsidy is over 25% of order revenue")
        if "wholesale" in str(ch.get("name", "")).lower() and c["price"] < 2 * landed:
            flags.append("wholesale price is under 2x landed cost, leaving little room once volume grows")
        if not ch.get("fee_source") or "PLACEHOLDER" in str(ch.get("fee_source")):
            flags.append("fee figures not sourced yet; check the platform's current fee page")
        rows.append({
            "channel": ch.get("name", ""), "price": c["price"], "units_per_order": u, "order_revenue": revenue,
            "landed_cost_per_order": landed * u, "fees_and_returns": pct_costs + c["payment_fee_fixed"] + c["fixed_fee_per_order"],
            "shipping_and_fulfilment_net": c["shipping_cost"] + c["fulfilment_per_order"] - c["shipping_charged"],
            "contribution_before_ads": before_ads, "ad_cost_per_order": c["ad_cost_per_order"],
            "contribution_after_ads": after_ads, "kept_per_unit_after_ads": after_ads / u,
            "margin_after_ads": after_ads / revenue if revenue else 0.0,
            "max_cac_per_order": max(0.0, before_ads),
            "break_even_roas": (revenue / before_ads) if before_ads > 0 else None,
            "price_for_target_margin": need_price,
            "fee_source": ch.get("fee_source", ""), "flags": flags,
        })
    best = max(rows, key=lambda r: r["kept_per_unit_after_ads"])
    return {"currency": data.get("currency", ""), "product": data.get("product", ""),
            "unit_cost": base_unit, "landed_unit_cost": landed, "target_margin_pct": target,
            "channels": rows, "best_channel": best["channel"]}


def product_md(r: dict) -> str:
    c = r["currency"]
    m = lambda x: "n/a" if x is None or x == float("inf") else f"{c} {x:,.2f}".strip()  # noqa: E731
    out = [f"# Per-channel unit margins: {r['product']}", "",
           f"Landed cost per unit: **{m(r['landed_unit_cost'])}** (target margin after ads: {r['target_margin_pct']:.0%})", "",
           "| Channel | Units/order | Order revenue | Landed cost | Fees + returns | Shipping/fulfilment (net) | Kept before ads | Ad cost | **Kept after ads** | **Per unit** | Margin | Break-even ROAS | Unit price for target |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for x in r["channels"]:
        roas = f"{x['break_even_roas']:.2f}" if x["break_even_roas"] else "n/a"
        out.append(f"| {x['channel']} | {x['units_per_order']:g} | {m(x['order_revenue'])} | {m(x['landed_cost_per_order'])} | {m(x['fees_and_returns'])} | "
                   f"{m(x['shipping_and_fulfilment_net'])} | {m(x['contribution_before_ads'])} | {m(x['ad_cost_per_order'])} | "
                   f"**{m(x['contribution_after_ads'])}** | **{m(x['kept_per_unit_after_ads'])}** | {x['margin_after_ads']:.0%} | {roas} | {m(x['price_for_target_margin'])} |")
    out += ["", f"Most kept per unit sold: **{r['best_channel']}**. Per-unit is the fair comparison when "
                "order sizes differ; also weigh the hours each channel takes (markets and wholesale cost time).", "",
            "- *Kept before ads* is also the most you can spend to win one order (max CAC).",
            "- *Break-even ROAS*: ad revenue divided by ad spend must beat this or ads lose money.",
            "- Returns are treated as a share of order revenue lost."]
    flagged = [(x["channel"], f) for x in r["channels"] for f in x["flags"]]
    if flagged:
        out += ["", "## Flags"] + [f"- **{ch}**: {f}" for ch, f in flagged]
    return "\n".join(out)


def service(a: argparse.Namespace) -> dict:
    if a.billable_hours <= 0 or a.weeks <= 0:
        raise ValueError("--billable-hours and --weeks must be positive")
    if not 0 <= a.buffer < 0.9:
        raise ValueError("--buffer must be between 0 and 0.9")
    hours = a.billable_hours * a.weeks
    need = a.target_income + a.overhead
    rate = need / hours / (1 - a.buffer)
    res = {"currency": a.currency, "target_income": a.target_income, "overhead": a.overhead,
           "billable_hours_per_week": a.billable_hours, "weeks": a.weeks, "annual_billable_hours": hours,
           "buffer": a.buffer, "hourly_rate": rate, "day_rate": rate * a.hours_per_day,
           "package_rates": {str(h): rate * h for h in (a.package_hours or [])}, "flags": []}
    if a.billable_hours > 30:
        res["flags"].append("more than 30 billable hours a week is rare once you count admin, sales and travel")
    if a.market_rate:
        res["market_rate"] = a.market_rate
        if rate > a.market_rate * 1.3:
            res["flags"].append(f"needed rate is over 30% above the market rate you gave ({a.market_rate:,.2f}); "
                                "you need a sharper niche, more billable hours, lower overhead or a lower income target")
        elif rate > a.market_rate * 1.1:
            res["flags"].append(f"needed rate is {rate / a.market_rate - 1:.0%} above the market rate you gave; "
                                "you need a clear reason to cost more (niche, proof of results, speed) or more billable hours")
        elif rate < a.market_rate * 0.8:
            res["flags"].append("needed rate is well below market; you can likely charge more")
    return res


def service_md(r: dict) -> str:
    c = r["currency"]
    m = lambda x: f"{c} {x:,.2f}".strip()  # noqa: E731
    out = ["# Service rate calculator", "", "| Item | Value |", "|---|---|",
           f"| Target income (before personal tax) | {m(r['target_income'])} |",
           f"| Business overhead per year | {m(r['overhead'])} |",
           f"| Billable hours | {r['billable_hours_per_week']}/week x {r['weeks']} weeks = {r['annual_billable_hours']:,.0f} |",
           f"| Buffer for slow months and unpaid work | {r['buffer']:.0%} |",
           f"| **Hourly rate needed** | **{m(r['hourly_rate'])}** |",
           f"| Day rate | {m(r['day_rate'])} |"]
    if "market_rate" in r:
        out.append(f"| Market rate (given) | {m(r['market_rate'])} |")
    for h, v in r["package_rates"].items():
        out.append(f"| Package of {h} hours | {m(v)} |")
    if r["flags"]:
        out += ["", "## Flags"] + [f"- {f}" for f in r["flags"]]
    out += ["", "Billable hours are hours a client pays for, not hours worked. Price packages by outcome where you can; "
                "this rate is the floor, not the target."]
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("product", help="per-channel unit margins for a physical or digital product")
    p.add_argument("input", nargs="?")
    p.add_argument("--template", action="store_true")
    p.add_argument("--json", action="store_true")
    s = sub.add_parser("service", help="hourly, day and package rate for a service business")
    s.add_argument("--target-income", type=float, required=True)
    s.add_argument("--overhead", type=float, default=0.0, help="business costs per year")
    s.add_argument("--billable-hours", type=float, required=True, help="paid hours per week")
    s.add_argument("--weeks", type=float, default=46, help="working weeks per year (default 46)")
    s.add_argument("--buffer", type=float, default=0.15, help="safety margin (default 0.15)")
    s.add_argument("--hours-per-day", type=float, default=7)
    s.add_argument("--package-hours", type=float, nargs="*")
    s.add_argument("--market-rate", type=float)
    s.add_argument("--currency", default="")
    s.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        if a.mode == "product":
            if a.template:
                print(json.dumps(PRODUCT_TEMPLATE, indent=2))
                return
            if not a.input:
                ap.error("product mode needs an input file (or --template)")
            with open(a.input, encoding="utf-8") as f:
                r = product(json.load(f))
            print(json.dumps(r, indent=2) if a.json else product_md(r))
        else:
            r = service(a)
            print(json.dumps(r, indent=2) if a.json else service_md(r))
    except ValueError as e:
        sys.exit(f"error: {e}")


if __name__ == "__main__":
    main()
