#!/usr/bin/env python3
"""Driver-based monthly financial model for a business starting from zero.

No historical financials needed. You describe the drivers (prices, how many
customers you expect to win, churn, costs, hires, funding) and this builds:

  model.xlsx   live-formula spreadsheet: change a blue input cell on the
               Assumptions sheet and the Model and Summary sheets update
  monthly.csv  the base-case month-by-month numbers
  summary.md   break-even, lowest cash point, funding needed, yearly totals,
               and a low / base / high scenario comparison

The Python calculation and the spreadsheet formulas follow the same logic, so
the summary matches what the spreadsheet shows.

Usage:
    python3 financial_model.py assumptions.json --out business/07-finance
    python3 financial_model.py --template > assumptions.json
    python3 financial_model.py assumptions.json --no-xlsx

Scenario multipliers (applied to every revenue stream):
    low:  volume x0.6, growth x0.5, churn x1.5, price x0.9
    high: volume x1.3, growth x1.3, churn x0.7
"""
from __future__ import annotations

import argparse
import copy
import csv
import datetime as dt
import json
import sys
from pathlib import Path

SCENARIOS = {
    "low": {"volume": 0.6, "growth": 0.5, "churn": 1.5, "price": 0.9},
    "base": {"volume": 1.0, "growth": 1.0, "churn": 1.0, "price": 1.0},
    "high": {"volume": 1.3, "growth": 1.3, "churn": 0.7, "price": 1.0},
}

TEMPLATE = {
    "company": "Example Co",
    "currency": "CAD",
    "months": 36,
    "start_month": "2027-01",
    "starting_cash": 1500,
    "startup_costs": [
        {"item": "Business name registration", "amount": 60},
        {"item": "Domain, email and website builder (first year)", "amount": 250},
        {"item": "Initial inventory or materials", "amount": 0},
    ],
    "payment_fee_pct": 0.029,
    "tax_rate": 0.0,
    "revenue_streams": [
        {"name": "Monthly plan", "type": "recurring", "price": 12, "new_customers_month1": 3,
         "monthly_growth": 0.08, "max_new_per_month": 40, "monthly_churn": 0.07, "cogs_pct": 0.10},
        {"name": "One-off setup service", "type": "one_time", "price": 150, "units_month1": 1,
         "monthly_growth": 0.05, "max_units_per_month": 6, "cogs_pct": 0.20},
    ],
    "fixed_costs": [
        {"item": "Software tools", "monthly": 40, "start_month": 1},
        {"item": "Accounting software", "monthly": 25, "start_month": 4},
    ],
    "marketing": {"monthly_budget": 250, "monthly_growth": 0.02, "start_month": 1},
    "team": [{"role": "Part-time contractor", "monthly": 600, "start_month": 13}],
    "funding": [{"month": 1, "amount": 0, "source": "Founder savings (already in starting cash)"}],
}


# ---------------------------------------------------------------- validation

def _n(obj: dict, key: str, default=None, lo=None, hi=None, where="") -> float | None:
    v = obj.get(key, default)
    if v is None:
        return None
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"{where}{key} must be a number, got {v!r}")
    if lo is not None and v < lo:
        raise ValueError(f"{where}{key}={v} is below {lo}")
    if hi is not None and v > hi:
        raise ValueError(f"{where}{key}={v} is above {hi}")
    return float(v)


def normalise(raw: dict) -> dict:
    a: dict = {}
    a["company"] = str(raw.get("company", "Company"))
    a["currency"] = str(raw.get("currency", ""))
    months = raw.get("months", 36)
    if not isinstance(months, int) or not 1 <= months <= 120:
        raise ValueError("months must be an integer from 1 to 120")
    a["months"] = months
    a["start_month"] = raw.get("start_month")
    a["starting_cash"] = _n(raw, "starting_cash", 0.0)
    a["payment_fee_pct"] = _n(raw, "payment_fee_pct", 0.0, 0, 1)
    a["tax_rate"] = _n(raw, "tax_rate", 0.0, 0, 1)

    a["startup_costs"] = [
        {"item": str(c.get("item", "")), "amount": _n(c, "amount", 0.0, 0, where="startup_costs: ")}
        for c in raw.get("startup_costs", [])
    ]

    streams = raw.get("revenue_streams") or []
    if not streams:
        raise ValueError("at least one revenue stream is required")
    a["revenue_streams"] = []
    for s in streams:
        w = f"revenue stream {s.get('name', '?')!r}: "
        t = s.get("type")
        if t == "recurring":
            a["revenue_streams"].append({
                "name": str(s.get("name", "Recurring")), "type": t,
                "price": _n(s, "price", None, 0, where=w),
                "volume1": _n(s, "new_customers_month1", None, 0, where=w),
                "growth": _n(s, "monthly_growth", 0.0, -1, 10, where=w),
                "cap": _n(s, "max_new_per_month", None, 0, where=w),
                "churn": _n(s, "monthly_churn", 0.0, 0, 1, where=w),
                "cogs_pct": _n(s, "cogs_pct", 0.0, 0, 1, where=w),
            })
        elif t == "one_time":
            a["revenue_streams"].append({
                "name": str(s.get("name", "Sales")), "type": t,
                "price": _n(s, "price", None, 0, where=w),
                "volume1": _n(s, "units_month1", None, 0, where=w),
                "growth": _n(s, "monthly_growth", 0.0, -1, 10, where=w),
                "cap": _n(s, "max_units_per_month", None, 0, where=w),
                "churn": 0.0,
                "cogs_pct": _n(s, "cogs_pct", 0.0, 0, 1, where=w),
            })
        else:
            raise ValueError(f"{w}type must be 'recurring' or 'one_time'")
        if a["revenue_streams"][-1]["price"] is None or a["revenue_streams"][-1]["volume1"] is None:
            raise ValueError(f"{w}price and month-1 volume are required")

    a["fixed_costs"] = [
        {"item": str(c.get("item", "")), "monthly": _n(c, "monthly", 0.0, 0, where="fixed_costs: "),
         "start": int(_n(c, "start_month", 1, 1, where="fixed_costs: "))}
        for c in raw.get("fixed_costs", [])
    ]
    m = raw.get("marketing", {}) or {}
    a["marketing"] = {"budget": _n(m, "monthly_budget", 0.0, 0), "growth": _n(m, "monthly_growth", 0.0, -1, 10),
                      "start": int(_n(m, "start_month", 1, 1))}
    a["team"] = [
        {"item": str(c.get("role", "")), "monthly": _n(c, "monthly", 0.0, 0, where="team: "),
         "start": int(_n(c, "start_month", 1, 1, where="team: "))}
        for c in raw.get("team", [])
    ]
    a["funding"] = [
        {"month": int(_n(f, "month", 1, 1, where="funding: ")), "amount": _n(f, "amount", 0.0, where="funding: "),
         "source": str(f.get("source", ""))}
        for f in raw.get("funding", [])
    ]
    return a


def apply_scenario(a: dict, name: str) -> dict:
    k = SCENARIOS[name]
    b = copy.deepcopy(a)
    for s in b["revenue_streams"]:
        s["price"] *= k["price"]
        s["volume1"] *= k["volume"]
        s["growth"] *= k["growth"]
        s["churn"] = min(1.0, s["churn"] * k["churn"])
    return b


# ---------------------------------------------------------------- simulation

def simulate(a: dict) -> dict:
    n = a["months"]
    ms = range(1, n + 1)
    lines: dict[str, list[float]] = {}
    revenue_keys, cogs_parts, new_rec_keys, active_keys = [], [], [], []

    for s in a["revenue_streams"]:
        vol = [s["volume1"] * (1 + s["growth"]) ** (m - 1) for m in ms]
        if s["cap"] is not None:
            vol = [min(v, s["cap"]) for v in vol]
        if s["type"] == "recurring":
            active, prev = [], 0.0
            for v in vol:
                prev = prev * (1 - s["churn"]) + v
                active.append(prev)
            lines[f"{s['name']}: new customers"] = vol
            lines[f"{s['name']}: active customers"] = active
            rev = [x * s["price"] for x in active]
            new_rec_keys.append(f"{s['name']}: new customers")
            active_keys.append(f"{s['name']}: active customers")
        else:
            lines[f"{s['name']}: units sold"] = vol
            rev = [x * s["price"] for x in vol]
        lines[f"{s['name']}: revenue"] = rev
        revenue_keys.append(f"{s['name']}: revenue")
        cogs_parts.append([r * s["cogs_pct"] for r in rev])

    total_rev = [sum(lines[k][i] for k in revenue_keys) for i in range(n)]
    cogs = [sum(p[i] for p in cogs_parts) for i in range(n)]
    fees = [r * a["payment_fee_pct"] for r in total_rev]
    gp = [total_rev[i] - cogs[i] - fees[i] for i in range(n)]

    opex_keys = []
    for c in a["fixed_costs"]:
        key = f"Fixed: {c['item']}"
        lines[key] = [c["monthly"] if m >= c["start"] else 0.0 for m in ms]
        opex_keys.append(key)
    mk = a["marketing"]
    lines["Marketing"] = [mk["budget"] * (1 + mk["growth"]) ** (m - mk["start"]) if m >= mk["start"] else 0.0 for m in ms]
    opex_keys.append("Marketing")
    for c in a["team"]:
        key = f"Team: {c['item']}"
        lines[key] = [c["monthly"] if m >= c["start"] else 0.0 for m in ms]
        opex_keys.append(key)
    opex = [sum(lines[k][i] for k in opex_keys) for i in range(n)]

    op = [gp[i] - opex[i] for i in range(n)]
    tax = [max(0.0, x) * a["tax_rate"] for x in op]
    net = [op[i] - tax[i] for i in range(n)]
    funding = [sum(f["amount"] for f in a["funding"] if f["month"] == m) for m in ms]
    startup_total = sum(c["amount"] for c in a["startup_costs"])
    startup = [startup_total if m == 1 else 0.0 for m in ms]
    ncf = [net[i] + funding[i] - startup[i] for i in range(n)]
    cash, prev = [], a["starting_cash"]
    for x in ncf:
        prev += x
        cash.append(prev)

    lines.update({
        "Total revenue": total_rev, "Cost of goods": cogs, "Payment fees": fees, "Gross profit": gp,
        "Total operating expenses": opex, "Operating profit": op, "Tax": tax, "Net profit": net,
        "Funding received": funding, "Startup costs": startup, "Net cash flow": ncf, "Ending cash": cash,
    })

    # sustained break-even: first month from which operating profit never goes negative again
    be = None
    for i in range(n):
        if all(x >= 0 for x in op[i:]):
            be = i + 1
            break
    low = min(cash)
    new_rec_total = sum(sum(lines[k]) for k in new_rec_keys)
    total_mkt = sum(lines["Marketing"])
    years = []
    for y in range((n + 11) // 12):
        sl = slice(y * 12, min(n, (y + 1) * 12))
        years.append({"year": y + 1, "revenue": sum(total_rev[sl]), "net_profit": sum(net[sl]),
                      "ending_cash": cash[sl][-1]})
    summary = {
        "break_even_month": be,
        "first_profitable_month": next((i + 1 for i, x in enumerate(op) if x >= 0), None),
        "lowest_cash": low,
        "lowest_cash_month": cash.index(low) + 1,
        "first_negative_cash_month": next((i + 1 for i, x in enumerate(cash) if x < 0), None),
        "funding_needed": max(0.0, -low),
        "ending_cash": cash[-1],
        "ending_active_customers": sum(lines[k][-1] for k in active_keys) if active_keys else None,
        "blended_cac": (total_mkt / new_rec_total) if new_rec_total > 0 else None,
        "startup_costs_total": startup_total,
        "years": years,
    }
    return {"lines": lines, "summary": summary, "revenue_keys": revenue_keys, "opex_keys": opex_keys,
            "new_rec_keys": new_rec_keys, "active_keys": active_keys}


def month_labels(a: dict) -> list[str]:
    s = a.get("start_month")
    if not s:
        return [f"M{m}" for m in range(1, a["months"] + 1)]
    y, mo = (int(p) for p in str(s).split("-")[:2])
    out = []
    for _ in range(a["months"]):
        out.append(f"{y:04d}-{mo:02d}")
        mo += 1
        if mo > 12:
            y, mo = y + 1, 1
    return out


# ---------------------------------------------------------------- spreadsheet

def build_xlsx(a: dict, path: Path, scenario_results: dict) -> None:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter as L

    n = a["months"]
    blue = Font(color="0000FF")
    bold = Font(bold=True)
    head = PatternFill("solid", fgColor="DDEBF7")
    money = '#,##0.00;[Red]-#,##0.00'
    count = '#,##0.0'
    pct = '0.0%'

    wb = Workbook()
    A = wb.active
    A.title = "Assumptions"
    A["A1"] = f"{a['company']}: assumptions"
    A["A1"].font = Font(bold=True, size=14)
    A["A2"] = "Blue cells are inputs. Change them and the Model and Summary sheets recalculate."
    ref: dict[str, str] = {}

    r = 4
    scalars = [
        ("currency", "Currency", a["currency"], None),
        ("starting_cash", "Starting cash", a["starting_cash"], money),
        ("fee", "Payment processing fee (% of revenue)", a["payment_fee_pct"], pct),
        ("tax", "Tax rate on profit (simplified)", a["tax_rate"], pct),
        ("mkt_budget", "Marketing budget in start month", a["marketing"]["budget"], money),
        ("mkt_growth", "Marketing budget monthly growth", a["marketing"]["growth"], pct),
        ("mkt_start", "Marketing start month #", a["marketing"]["start"], None),
    ]
    for key, label, val, fmt in scalars:
        A.cell(r, 1, label)
        c = A.cell(r, 2, val)
        c.font = blue
        if fmt:
            c.number_format = fmt
        ref[key] = f"Assumptions!$B${r}"
        r += 1

    def table(title: str, headers: list[str], rows: list[list], fmts: list[str | None]) -> tuple[int, int]:
        nonlocal r
        r += 1
        A.cell(r, 1, title).font = bold
        r += 1
        for j, h in enumerate(headers, 1):
            c = A.cell(r, j, h)
            c.font = bold
            c.fill = head
        r += 1
        first = r
        for row in rows:
            for j, v in enumerate(row, 1):
                c = A.cell(r, j, v)
                if j > 1 or title.startswith("Funding"):
                    c.font = blue
                if fmts[j - 1] and isinstance(v, (int, float)):
                    c.number_format = fmts[j - 1]
            r += 1
        return first, r - 1

    sc_rows = [[c["item"], c["amount"]] for c in a["startup_costs"]] or [["(none)", 0]]
    f0, f1 = table("Startup costs (paid in month 1)", ["Item", "Amount"], sc_rows, [None, money])
    A.cell(r, 1, "Total startup costs").font = bold
    A.cell(r, 2, f"=SUM(B{f0}:B{f1})").number_format = money
    ref["startup_total"] = f"Assumptions!$B${r}"
    r += 1

    stream_rows = []
    for s in a["revenue_streams"]:
        stream_rows.append([s["name"], s["type"], s["price"], s["volume1"], s["growth"],
                            s["cap"] if s["cap"] is not None else "", s["churn"], s["cogs_pct"]])
    s0, _ = table("Revenue streams",
                  ["Name", "Type", "Price", "Month-1 volume (new customers or units)", "Monthly growth",
                   "Max per month (blank = no cap)", "Monthly churn (recurring only)", "Cost of goods %"],
                  stream_rows, [None, None, money, count, pct, count, pct, pct])

    fc_rows = [[c["item"], c["monthly"], c["start"]] for c in a["fixed_costs"]]
    fc0 = table("Fixed monthly costs", ["Item", "Monthly", "Start month #"], fc_rows, [None, money, None])[0] if fc_rows else None
    tm_rows = [[c["item"], c["monthly"], c["start"]] for c in a["team"]]
    tm0 = table("Team and contractors", ["Role", "Monthly cost", "Start month #"], tm_rows, [None, money, None])[0] if tm_rows else None
    fd_rows = [[f["month"], f["amount"], f["source"]] for f in a["funding"]] or [["", 0, "(none)"]]
    fd0, fd1 = table("Funding received", ["Month #", "Amount", "Source"], fd_rows, [None, money, None])
    ref["fund_months"] = f"Assumptions!$A${fd0}:$A${fd1}"
    ref["fund_amounts"] = f"Assumptions!$B${fd0}:$B${fd1}"

    A.column_dimensions["A"].width = 44
    for col in "BCDEFGH":
        A.column_dimensions[col].width = 18

    # ---- Model sheet
    M = wb.create_sheet("Model")
    last = L(n + 1)
    M["A1"] = "Month #"
    M["A2"] = "Month"
    M["A1"].font = M["A2"].font = bold
    for i, lab in enumerate(month_labels(a)):
        M.cell(1, i + 2, i + 1).font = bold
        M.cell(2, i + 2, lab).font = bold
    mr = 3
    rows: dict[str, int] = {}

    def add(label: str, fn, fmt=money, is_bold=False) -> int:
        nonlocal mr
        M.cell(mr, 1, label).font = bold if is_bold else Font()
        for i in range(n):
            col = L(i + 2)
            c = M.cell(mr, i + 2, fn(col, i))
            c.number_format = fmt
            if is_bold:
                c.font = bold
        rows[label] = mr
        mr += 1
        return mr - 1

    def section(title: str) -> None:
        nonlocal mr
        mr += 1
        M.cell(mr, 1, title).font = Font(bold=True, color="1F4E78")
        mr += 1

    section("Revenue")
    rev_rows, cogs_terms, new_rows, active_rows = [], [], [], []
    for k, s in enumerate(a["revenue_streams"]):
        ar = s0 + k
        price, vol1, g, cap, churn, cg = (f"Assumptions!$C${ar}", f"Assumptions!$D${ar}", f"Assumptions!$E${ar}",
                                          f"Assumptions!$F${ar}", f"Assumptions!$G${ar}", f"Assumptions!$H${ar}")
        vol = lambda col, i, vol1=vol1, g=g, cap=cap: (  # noqa: E731
            f'=IF({cap}="",{vol1}*(1+{g})^({col}$1-1),MIN({vol1}*(1+{g})^({col}$1-1),{cap}))')
        if s["type"] == "recurring":
            nr = add(f"{s['name']}: new customers", vol, count)
            act = mr

            def active(col, i, nr=nr, act=act, churn=churn):
                if i == 0:
                    return f"={col}{nr}"
                return f"={L(i + 1)}{act}*(1-{churn})+{col}{nr}"
            add(f"{s['name']}: active customers", active, count)
            rr = add(f"{s['name']}: revenue", lambda col, i, act=act, price=price: f"={col}{act}*{price}")
            new_rows.append(nr)
            active_rows.append(act)
        else:
            ur = add(f"{s['name']}: units sold", vol, count)
            rr = add(f"{s['name']}: revenue", lambda col, i, ur=ur, price=price: f"={col}{ur}*{price}")
        rev_rows.append(rr)
        cogs_terms.append((rr, cg))

    tr = add("Total revenue", lambda col, i: "=" + "+".join(f"{col}{x}" for x in rev_rows), is_bold=True)
    cr = add("Cost of goods", lambda col, i: "=" + "+".join(f"{col}{x}*{c}" for x, c in cogs_terms))
    fr = add("Payment fees", lambda col, i: f"={col}{tr}*{ref['fee']}")
    gr = add("Gross profit", lambda col, i: f"={col}{tr}-{col}{cr}-{col}{fr}", is_bold=True)

    section("Operating expenses")
    ox = []
    for k, c in enumerate(a["fixed_costs"]):
        rr_ = fc0 + k
        ox.append(add(f"Fixed: {c['item']}", lambda col, i, rr_=rr_:
                      f"=IF({col}$1>=Assumptions!$C${rr_},Assumptions!$B${rr_},0)"))
    ox.append(add("Marketing", lambda col, i:
                  f"=IF({col}$1>={ref['mkt_start']},{ref['mkt_budget']}*(1+{ref['mkt_growth']})^({col}$1-{ref['mkt_start']}),0)"))
    for k, c in enumerate(a["team"]):
        rr_ = tm0 + k
        ox.append(add(f"Team: {c['item']}", lambda col, i, rr_=rr_:
                      f"=IF({col}$1>=Assumptions!$C${rr_},Assumptions!$B${rr_},0)"))
    oxr = add("Total operating expenses", lambda col, i: "=" + "+".join(f"{col}{x}" for x in ox), is_bold=True)

    section("Profit and cash")
    opr = add("Operating profit", lambda col, i: f"={col}{gr}-{col}{oxr}", is_bold=True)
    txr = add("Tax", lambda col, i: f"=MAX(0,{col}{opr})*{ref['tax']}")
    npr = add("Net profit", lambda col, i: f"={col}{opr}-{col}{txr}", is_bold=True)
    fdr = add("Funding received", lambda col, i: f"=SUMIF({ref['fund_months']},{col}$1,{ref['fund_amounts']})")
    sur = add("Startup costs", lambda col, i: f"=IF({col}$1=1,{ref['startup_total']},0)")
    ncr = add("Net cash flow", lambda col, i: f"={col}{npr}+{col}{fdr}-{col}{sur}")
    chr_ = mr

    def cash(col, i):
        if i == 0:
            return f"={ref['starting_cash']}+{col}{ncr}"
        return f"={L(i + 1)}{chr_}+{col}{ncr}"
    add("Ending cash", cash, is_bold=True)

    section("Helpers")
    hr = mr

    def sustained(col, i):
        if i == n - 1:
            return f"={col}{opr}>=0"
        return f"=AND({col}{opr}>=0,{L(i + 3)}{hr})"
    add("Profitable from this month on?", sustained, "General")
    ngr = add("Cash below zero?", lambda col, i: f"={col}{chr_}<0", "General")
    if new_rows:
        nrt = add("Total new recurring customers", lambda col, i: "=" + "+".join(f"{col}{x}" for x in new_rows), count)
    M.column_dimensions["A"].width = 40
    M.freeze_panes = "B3"

    # ---- Summary sheet
    S = wb.create_sheet("Summary", 0)
    S["A1"] = f"{a['company']}: financial summary ({a['currency']})"
    S["A1"].font = Font(bold=True, size=14)
    S["A2"] = "Formulas read from the Model sheet. Edit inputs on the Assumptions sheet."
    rng = lambda row: f"Model!$B${row}:${last}${row}"  # noqa: E731
    items = [
        ("Break-even month # (profitable from then on)", f'=IFERROR(MATCH(TRUE,{rng(hr)},0),"Not within model")', "General"),
        ("Lowest cash balance", f"=MIN({rng(chr_)})", money),
        ("Month # of lowest cash", f"=MATCH(MIN({rng(chr_)}),{rng(chr_)},0)", "General"),
        ("Outside funding needed beyond plan", f"=MAX(0,-MIN({rng(chr_)}))", money),
        ("First month # cash goes negative", f'=IFERROR(MATCH(TRUE,{rng(ngr)},0),"Never")', "General"),
        ("Ending cash", f"=Model!${last}${chr_}", money),
        ("Total startup costs", f"={ref['startup_total']}", money),
    ]
    if new_rows:
        items.append(("Ending active subscribers", "=" + "+".join(f"Model!${last}${x}" for x in active_rows), count))
        items.append(("Blended CAC (marketing / new subscribers)",
                      f'=IFERROR(SUM({rng(rows["Marketing"])})/SUM({rng(nrt)}),"n/a")', money))
    sr = 4
    for label, f, fmt in items:
        S.cell(sr, 1, label)
        c = S.cell(sr, 2, f)
        c.number_format = fmt
        sr += 1
    sr += 1
    for j, h in enumerate(["Year", "Revenue", "Net profit", "Ending cash"], 1):
        c = S.cell(sr, j, h)
        c.font = bold
        c.fill = head
    sr += 1
    for y in range((n + 11) // 12):
        c0, c1 = L(2 + y * 12), L(1 + min(n, (y + 1) * 12))
        S.cell(sr, 1, f"Year {y + 1}")
        S.cell(sr, 2, f"=SUM(Model!{c0}{tr}:{c1}{tr})").number_format = money
        S.cell(sr, 3, f"=SUM(Model!{c0}{npr}:{c1}{npr})").number_format = money
        S.cell(sr, 4, f"=Model!{c1}{chr_}").number_format = money
        sr += 1
    S.column_dimensions["A"].width = 46
    for col in "BCD":
        S.column_dimensions[col].width = 18

    # ---- Scenarios sheet (static values computed in Python)
    X = wb.create_sheet("Scenarios")
    X["A1"] = "Scenario comparison (static values, recalculate by re-running financial_model.py)"
    X["A1"].font = bold
    hdr = ["Metric"] + list(scenario_results)
    for j, h in enumerate(hdr, 1):
        c = X.cell(3, j, h)
        c.font = bold
        c.fill = head
    for i, (label, fn) in enumerate(_scenario_metrics(), 4):
        X.cell(i, 1, label)
        for j, name in enumerate(scenario_results, 2):
            X.cell(i, j, fn(scenario_results[name]["summary"]))
    X.cell(4 + len(_scenario_metrics()) + 1, 1,
           "low: volume x0.6, growth x0.5, churn x1.5, price x0.9. high: volume x1.3, growth x1.3, churn x0.7.")
    X.column_dimensions["A"].width = 40
    wb.save(path)


def _scenario_metrics():
    def r(v):
        return round(v, 2) if isinstance(v, float) else v
    return [
        ("Break-even month #", lambda s: s["break_even_month"] or "Not within model"),
        ("Lowest cash", lambda s: r(s["lowest_cash"])),
        ("Outside funding needed", lambda s: r(s["funding_needed"])),
        ("Ending cash", lambda s: r(s["ending_cash"])),
        ("Year 1 revenue", lambda s: r(s["years"][0]["revenue"])),
        ("Final-year revenue", lambda s: r(s["years"][-1]["revenue"])),
    ]


# ---------------------------------------------------------------- reports

def money_fmt(x: float | None, cur: str) -> str:
    if x is None:
        return "n/a"
    return f"{cur} {x:,.0f}".strip()


def summary_md(a: dict, results: dict) -> str:
    cur = a["currency"]
    b = results["base"]["summary"]
    out = [f"# Financial model summary: {a['company']}", "",
           f"{a['months']}-month driver-based model, base case unless noted. Currency: {cur or 'not set'}.", "",
           "| Metric | Base case |", "|---|---|"]
    out.append(f"| Break-even month (profitable from then on) | {b['break_even_month'] or 'Not within model'} |")
    out.append(f"| Lowest cash balance | {money_fmt(b['lowest_cash'], cur)} (month {b['lowest_cash_month']}) |")
    out.append(f"| Outside funding needed beyond plan | {money_fmt(b['funding_needed'], cur)} |")
    out.append(f"| Cash first goes negative | {('month ' + str(b['first_negative_cash_month'])) if b['first_negative_cash_month'] else 'never'} |")
    out.append(f"| Ending cash | {money_fmt(b['ending_cash'], cur)} |")
    out.append(f"| One-time startup costs | {money_fmt(b['startup_costs_total'], cur)} |")
    if b["ending_active_customers"] is not None:
        out.append(f"| Ending active subscribers | {b['ending_active_customers']:,.0f} |")
        out.append(f"| Blended CAC | {money_fmt(b['blended_cac'], cur)} |")
    out += ["", "| Year | Revenue | Net profit | Ending cash |", "|---|---|---|---|"]
    for y in b["years"]:
        out.append(f"| {y['year']} | {money_fmt(y['revenue'], cur)} | {money_fmt(y['net_profit'], cur)} | {money_fmt(y['ending_cash'], cur)} |")
    out += ["", "## Scenarios", "", "| Metric | " + " | ".join(results) + " |", "|---|" + "---|" * len(results)]
    for label, fn in _scenario_metrics():
        vals = []
        for name in results:
            v = fn(results[name]["summary"])
            vals.append(money_fmt(v, cur) if isinstance(v, float) else str(v))
        out.append(f"| {label} | " + " | ".join(vals) + " |")
    warnings = []
    if b["funding_needed"] > 0:
        warnings.append(f"Base case runs out of cash in month {b['first_negative_cash_month']}; "
                        f"you need about {money_fmt(b['funding_needed'], cur)} more than planned, or lower costs.")
    lo = results["low"]["summary"]
    if lo["funding_needed"] > b["funding_needed"] * 2 and lo["funding_needed"] > 0:
        warnings.append(f"Low case needs {money_fmt(lo['funding_needed'], cur)}: the plan is fragile if growth disappoints.")
    if b["break_even_month"] is None:
        warnings.append("Base case never becomes sustainably profitable inside the model window.")
    rec_prices = [s["price"] for s in a["revenue_streams"] if s["type"] == "recurring"]
    if b["blended_cac"] is not None and rec_prices and b["blended_cac"] < min(rec_prices):
        warnings.append(
            f"Blended CAC ({money_fmt(b['blended_cac'], cur)}) is below one month's price. That only happens "
            "with strong word of mouth or an existing audience; otherwise the growth rate is doing work the "
            "marketing budget can't. Check the customer-acquisition assumptions.")
    if warnings:
        out += ["", "## Warnings"] + [f"- {w}" for w in warnings]
    out += ["", "Simplifications: tax is a flat rate on positive monthly operating profit; no sales tax, "
                "depreciation, payment timing or inventory carrying. Fine for planning, not for filing."]
    return "\n".join(out)


def _scale_streams(key: str):
    def f(a: dict, k: float) -> None:
        for s in a["revenue_streams"]:
            s[key] = min(1.0, s[key] * k) if key in ("churn", "cogs_pct") else s[key] * k
    return f


def _scale_costs(a: dict, k: float) -> None:
    for c in a["fixed_costs"] + a["team"]:
        c["monthly"] *= k


def _scale_marketing(a: dict, k: float) -> None:
    a["marketing"]["budget"] *= k


SENS_DRIVERS = [
    ("Price", _scale_streams("price")),
    ("Month-1 volume", _scale_streams("volume1")),
    ("Monthly growth rate", _scale_streams("growth")),
    ("Churn", _scale_streams("churn")),
    ("Cost of goods %", _scale_streams("cogs_pct")),
    ("Fixed and team costs", _scale_costs),
    ("Marketing budget (cost only)", _scale_marketing),
]


def sensitivity(a: dict, delta: float = 0.2) -> list[dict]:
    """Move each driver down and up by delta on the base case; rank by effect on ending cash."""
    out = []
    has_churn = any(s["churn"] > 0 for s in a["revenue_streams"])
    for label, fn in SENS_DRIVERS:
        if label == "Churn" and not has_churn:
            continue
        res = {}
        for side, k in (("down", 1 - delta), ("up", 1 + delta)):
            b = copy.deepcopy(a)
            fn(b, k)
            res[side] = simulate(b)["summary"]
        swing = abs(res["up"]["ending_cash"] - res["down"]["ending_cash"])
        out.append({"driver": label, "down": res["down"], "up": res["up"], "swing": swing})
    out.sort(key=lambda r: -r["swing"])
    return out


def sensitivity_md(a: dict, rows: list[dict], delta: float = 0.2) -> str:
    cur = a["currency"]
    out = ["", f"## Sensitivity (each driver moved -{delta:.0%} and +{delta:.0%}, base case)", "",
           "| Driver | Ending cash at -/+ | Funding needed at -/+ | Break-even month at -/+ |", "|---|---|---|---|"]
    for r in rows:
        d, u = r["down"], r["up"]
        be = lambda s: str(s["break_even_month"] or "none")  # noqa: E731
        out.append(f"| {r['driver']} | {money_fmt(d['ending_cash'], cur)} / {money_fmt(u['ending_cash'], cur)} | "
                   f"{money_fmt(d['funding_needed'], cur)} / {money_fmt(u['funding_needed'], cur)} | "
                   f"{be(d)} / {be(u)} |")
    top = ", ".join(r["driver"] for r in rows[:3])
    out += ["", f"Biggest drivers of the outcome: **{top}**. Test these assumptions first.",
            "Note: customer volumes are inputs, not driven by marketing spend, so the marketing row only shows "
            "the cost side. Check the blended CAC is believable."]
    return "\n".join(out)


def write_csv(a: dict, sim: dict, path: Path) -> None:
    labels = month_labels(a)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Line"] + labels)
        for k, vals in sim["lines"].items():
            w.writerow([k] + [round(v, 2) for v in vals])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", nargs="?")
    ap.add_argument("--out", default=".", help="output folder (default: current folder)")
    ap.add_argument("--no-xlsx", action="store_true")
    ap.add_argument("--template", action="store_true", help="print an example assumptions file")
    ap.add_argument("--json", action="store_true", help="print scenario summaries as JSON")
    ap.add_argument("--sensitivity", action="store_true", help="add a +/-20%% driver sensitivity table")
    args = ap.parse_args()
    if args.template:
        print(json.dumps(TEMPLATE, indent=2))
        return
    if not args.input:
        ap.error("assumptions file required (or --template)")
    with open(args.input, encoding="utf-8") as f:
        raw = json.load(f)
    try:
        a = normalise(raw)
    except (ValueError, TypeError) as e:
        sys.exit(f"error: {e}")

    results = {name: simulate(apply_scenario(a, name)) for name in ("low", "base", "high")}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    write_csv(a, results["base"], out / "monthly.csv")
    md = summary_md(a, results)
    if args.sensitivity:
        md += "\n" + sensitivity_md(a, sensitivity(a))
    (out / "summary.md").write_text(md + "\n", encoding="utf-8")
    written = ["monthly.csv", "summary.md"]
    if not args.no_xlsx:
        try:
            build_xlsx(a, out / "model.xlsx", results)
            written.append("model.xlsx")
        except ImportError:
            print("note: openpyxl not installed, skipped model.xlsx (pip install openpyxl)", file=sys.stderr)
    if args.json:
        print(json.dumps({k: v["summary"] for k, v in results.items()}, indent=2))
    else:
        print(md)
    print(f"\nWrote {', '.join(written)} to {out.resolve()}", file=sys.stderr)


if __name__ == "__main__":
    main()
