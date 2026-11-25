# Idea scan

Use when the founder has no idea yet, wants more options, or a Quick scan killed everything. Instead of brainstorming in the chat, three departments scan for real problems in parallel, each from a different angle, and return ideas in one JSON format that HQ scores with `idea_lens.py`.

## The three scans (launch in one message)

| Scan | Department role file | Writes to | Angle |
|---|---|---|---|
| Business problems | `biz-market-analyst` | `01-market/ideas-business-problems.md` + `.json` | The biggest problems local and national small businesses report right now (business associations, statistics agencies, chambers), then services that solve them |
| People and groups | `biz-customer-researcher` | `03-customers/ideas-people-problems.md` + `.json` | The biggest problems of people and groups where the founder lives (census profile, regional reports): older adults and caregivers, newcomers, students and parents, homeowners and renters, nonprofits, clubs, people with disabilities |
| Proven elsewhere | `biz-competitor-analyst` | `02-competitors/ideas-ai-arbitrage.md` + `.json` | Services with real traction in other cities or countries that are missing or rare where the founder is |

Each department follows its own role file's sourcing and honesty rules, but this task replaces its normal deliverables. Tell every scan:
- what was already scanned (point at `EXECUTIVE-SUMMARY.md` or the brief) so ideas don't repeat;
- the founder's constraints (place, hours, budget, skills, age, availability horizon);
- to design 5-7 ideas where the founder's edge (often AI and automation) does most of the work, with recurring revenue preferred;
- to check availability for each idea: who already offers it nearby and nationally, at what dated price, and free alternatives;
- to flag regulated activities (licences, legal, financial, medical, immigration advice, working with vulnerable people) and say what the founder can legally do;
- to return the JSON below and validate it with `python3 -m json.tool`.

## JSON each scan returns

```
{"ideas": [{
  "id": "B1", "name": "short name", "customer": "who pays", "problem": "one line",
  "solution": "one line: what the service does and how AI does the work",
  "founder_role": "what the founder still has to do",
  "ease": 1-5,            how easy for THIS founder to start and deliver (5 = this week, current skills, tiny budget)
  "money_ceiling": 1-5,   realistic upside (1 = pocket money, 3 = solid local income, 5 = grows beyond the area and one person)
  "stickiness": 1-5,      how consistent the money is (5 = mostly monthly, clients rarely leave)
  "ai_share": 0-1,        share of delivery work AI and automation can do
  "setup_price": 0+, "monthly_price": 0+,
  "sales_hours_per_client": 0+, "setup_hours": 0+, "monthly_hours": 0+,
  "new_clients": [m1, m2, m3],   conservative, for a founder starting from zero
  "monthly_churn": 0-1, "local_competition": "low" | "medium" | "high",
  "evidence": "key sources", "flags": "regulation, ethics, platform or other risks"
}]}
```

Use prefixes B (business problems), P (people and groups), A (proven elsewhere). HQ adds its own combinations with H or C ids, and founder-supplied pitches with F ids, in `00-hq/lens-*.json`.

## Scoring (HQ)

1. `python3 SKILL_DIR/scripts/idea_lens.py 00-hq/lens-*.json 01-market/ideas-*.json 03-customers/ideas-*.json 02-competitors/ideas-*.json --hours <founder hours> --currency <code> > 00-hq/lens-ranking.md`
2. Fairness check, because each agent rated its own ideas: rerun with `--same-ramp 1,1,2`. If the top ideas change, say so and say why.
3. Read the evidence behind the top 3-5 yourself and spot-check their load-bearing claims at the source.
4. Run the go / pivot / kill scorecard (`scorecard.py`) on the top 2-3. The lens says whether an idea suits the founder; the scorecard says whether the evidence supports building it. Show both.
5. If HQ combines ideas (two ideas sell to the same customer), score the combination as its own entry and say it's HQ's synthesis.
6. Update `EXECUTIVE-SUMMARY.md` with the ranking, the recommended one or two, the ideas dropped and why (especially regulated ones), and the cheapest tests.

## The four lens measures (what the founder sees)

- **Idiot index**: ease for this founder x money ceiling, after Hormozi's chart of difficulty vs income. Quadrants: sweet spot, starter cash, hard but big, middle, avoid.
- **First quarter**: revenue and clients in months 1-3, simulated against the founder's real hours.
- **Stickiness**: how consistent the money is.
- **AI compatibility**: share of the work AI can do. High cuts both ways: if AI does most of it, competitors and the client can too, so the moat has to be trust, niche or relationships.
