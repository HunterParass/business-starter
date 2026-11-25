#!/usr/bin/env python3
"""Check whether domain names are registered, using the registries' own RDAP servers.

Most "domain brainstorm" prompts tell the model to check availability but give it no way
to do it, so it guesses. This script asks the registry. RDAP is the official successor to
WHOIS: the registry answers 200 (registered) or 404 (not registered). The server for each
TLD comes from IANA's bootstrap file, so no API key or account is needed.

Usage:
    python3 domain_check.py brightfix fixmystore --tlds com,ca,co     # bare names x TLDs
    python3 domain_check.py brightfix.com fixmystore.ca               # full domains
    python3 domain_check.py --file names.txt --tlds com,ca [--json]

Statuses:
    registered      the registry has a record; someone owns it (maybe for sale, but not free)
    not registered  the registry has no record; usually registrable, but reserved or
                    premium names can still be blocked or cost more, so confirm at a registrar
    unknown         no RDAP server for that TLD, a network error, or rate limiting

A name being free as a domain says nothing about trademarks or business names. Check those
separately (CIPO in Canada, USPTO in the US, and your province or state's business registry).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

BOOTSTRAP_URL = "https://data.iana.org/rdap/dns.json"
FALLBACK_BASE = "https://rdap.org/"
CACHE = Path(tempfile.gettempdir()) / "business-starter-rdap-dns.json"
CACHE_MAX_AGE = 24 * 3600
LABEL = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$")
UA = "business-starter-domain-check/1.0 (+https://github.com/HunterParass/business-starter)"


def http_get(url: str, timeout: float = 10.0) -> tuple[int, str]:
    """GET a URL; return (status, body). 4xx/5xx come back as statuses, not exceptions."""
    req = urllib.request.Request(url, headers={"Accept": "application/rdap+json, application/json", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""


def normalise_label(name: str) -> str:
    name = name.strip().lower()
    try:
        name = name.encode("idna").decode("ascii")
    except UnicodeError as e:
        raise ValueError(f"not a valid name: {name!r}") from e
    return name


def expand(names: list[str], tlds: list[str]) -> list[str]:
    """Turn bare names and full domains into a de-duplicated list of domains."""
    out: list[str] = []
    for raw in names:
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        raw = re.sub(r"^https?://", "", raw.lower()).split("/")[0]
        if raw.startswith("www."):
            raw = raw[4:]
        candidates = [raw] if "." in raw else [f"{raw}.{t}" for t in tlds]
        for d in candidates:
            labels = [normalise_label(x) for x in d.split(".")]
            if len(labels) < 2 or not all(LABEL.match(x) for x in labels):
                raise ValueError(f"not a valid domain: {d!r} (letters, digits and hyphens only; no hyphen at the start or end)")
            dom = ".".join(labels)
            if dom not in out:
                out.append(dom)
    return out


def quality_flags(domain: str) -> list[str]:
    """Simple, deterministic warnings about the name itself (not legal advice)."""
    label = domain.split(".")[0]
    flags = []
    if len(label) > 15:
        flags.append("long (over 15 characters)")
    if "-" in label:
        flags.append("hyphen (people forget it when they say it)")
    if any(c.isdigit() for c in label):
        flags.append("number (four or 4?)")
    if label.startswith("xn--"):
        flags.append("non-English characters (hard to type)")
    return flags


def load_bootstrap(fetch=http_get) -> dict[str, str]:
    """Map each TLD to its RDAP base URL, from IANA's bootstrap file (cached for a day)."""
    text = None
    try:
        if CACHE.exists() and time.time() - CACHE.stat().st_mtime < CACHE_MAX_AGE:
            text = CACHE.read_text()
    except OSError:
        text = None
    if text is None:
        try:
            status, text = fetch(BOOTSTRAP_URL)
        except Exception:
            return {}
        if status != 200:
            return {}
        try:
            CACHE.write_text(text)
        except OSError:
            pass
    try:
        data = json.loads(text)
    except ValueError:
        return {}
    table = {}
    for tlds, urls in data.get("services", []):
        https = [u for u in urls if u.startswith("https://")] or urls
        if not https:
            continue
        base = https[0] if https[0].endswith("/") else https[0] + "/"
        for t in tlds:
            table[t.lower()] = base
    return table


def lookup(domain: str, bootstrap: dict[str, str], fetch=http_get) -> dict:
    tld = domain.rsplit(".", 1)[1]
    base = bootstrap.get(tld)
    via = "registry RDAP"
    if base is None:
        if bootstrap:
            return {"domain": domain, "status": "unknown",
                    "detail": f"the .{tld} registry has no RDAP service listed with IANA; check at a registrar",
                    "flags": quality_flags(domain)}
        base, via = FALLBACK_BASE, "rdap.org (IANA list unavailable)"
    url = f"{base}domain/{domain}"
    status, body = None, ""
    for attempt in range(2):
        try:
            status, body = fetch(url)
        except Exception as e:  # network error, timeout, DNS failure
            return {"domain": domain, "status": "unknown", "detail": f"lookup failed: {type(e).__name__}",
                    "flags": quality_flags(domain)}
        if status != 429:
            break
        time.sleep(2)
    row = {"domain": domain, "flags": quality_flags(domain), "source": via}
    if status == 200:
        row["status"] = "registered"
        row["detail"] = registered_detail(body)
    elif status == 404:
        row["status"] = "not registered"
        row["detail"] = "no registry record; confirm price and availability at a registrar"
    else:
        row["status"] = "unknown"
        row["detail"] = f"registry answered HTTP {status}"
    return row


def registered_detail(body: str) -> str:
    try:
        data = json.loads(body)
    except ValueError:
        return "registry has a record"
    events = {e.get("eventAction"): (e.get("eventDate") or "")[:10] for e in data.get("events", []) if isinstance(e, dict)}
    parts = []
    if events.get("registration"):
        parts.append(f"registered {events['registration']}")
    if events.get("expiration"):
        parts.append(f"expires {events['expiration']}")
    return ", ".join(parts) or "registry has a record"


def check(domains: list[str], fetch=http_get, pause: float = 0.3) -> list[dict]:
    bootstrap = load_bootstrap(fetch)
    rows = []
    for i, d in enumerate(domains):
        if i and pause:
            time.sleep(pause)
        rows.append(lookup(d, bootstrap, fetch))
    return rows


def to_md(rows: list[dict]) -> str:
    order = {"not registered": 0, "unknown": 1, "registered": 2}
    rows = sorted(rows, key=lambda r: (order.get(r["status"], 3), r["domain"]))
    out = [f"# Domain check ({time.strftime('%Y-%m-%d')})", "",
           "| Domain | Status | Detail | Name flags |", "|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r['domain']} | {r['status']} | {r['detail']} | {', '.join(r['flags']) or '-'} |")
    free = sum(r["status"] == "not registered" for r in rows)
    unknown = sum(r["status"] == "unknown" for r in rows)
    out += ["", f"{free} not registered, {sum(r['status'] == 'registered' for r in rows)} registered, {unknown} unknown.", "",
            "- \"Not registered\" comes from the registry itself, but reserved and premium names can still be blocked "
            "or cost more. Confirm at a registrar before you rely on a name, and register it in the business's or "
            "founder's own name.",
            "- A free domain is not a free name. Check trademarks (CIPO in Canada, USPTO in the US) and your "
            "province or state's business-name registry, and look for the same name on the social platforms you'll use."]
    if unknown:
        out.append("- Unknown means the lookup couldn't answer (no RDAP for that TLD, no network, or rate limiting). "
                   "Check those at a registrar.")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*", help="bare names (combined with --tlds) or full domains")
    ap.add_argument("--file", help="text file with one name or domain per line")
    ap.add_argument("--tlds", default="com", help="comma-separated TLDs for bare names (default: com)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    names = list(a.names)
    try:
        if a.file:
            names += Path(a.file).read_text().splitlines()
        tlds = [t.strip().lstrip(".").lower() for t in a.tlds.split(",") if t.strip()]
        if not tlds:
            raise ValueError("--tlds is empty")
        domains = expand(names, tlds)
        if not domains:
            raise ValueError("give at least one name or domain")
        if len(domains) > 60:
            raise ValueError(f"{len(domains)} domains is too many for one run; shortlist first (max 60)")
    except (ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    rows = check(domains)
    print(json.dumps(rows, indent=2) if a.json else to_md(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
