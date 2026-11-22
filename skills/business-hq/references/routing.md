# Operate mode routing

Once the plan exists (or the business is already running), the founder asks questions and HQ routes them. Narrow questions go to one department. Cross-functional ones go to several in parallel, and HQ merges the answers into one recommendation.

| Founder asks about | Department(s) |
|---|---|
| Is this idea / new product line worth it? | market + competitors + customers (quick), then scorecard |
| Who are my competitors now, what did they change? | competitors |
| Who exactly is my customer, why aren't they buying? | customers |
| I have interview notes / survey results / reviews to analyse | customers |
| Pricing, packaging, discounts, the offer, business model change | strategist (+ finance to model the impact) |
| Name, logo direction, website copy, positioning, packaging look | brand |
| What to build next, MVP, features, prototypes, tools | product |
| Cash, runway, can I afford X, budget, financial model | finance |
| Last month's numbers / are we on track? | HQ monthly check-in (`plan_vs_actual.py`), then finance if off track |
| Registering, taxes, licences, permits, contracts, privacy, trademarks, labelling | legal |
| How do I get customers, launch, ads, email list, SEO, local listings | marketing |
| What should I post, TikToks, Reels, Shorts, hooks, going viral, influencers, UGC, community | content |
| Outreach, sales scripts, proposals, closing deals, partnerships | sales |
| Where to sell, Etsy, Amazon, TikTok Shop, Shopify, listings, product photos, shipping, returns, stock and reorders, wholesale, markets | commerce |
| Reviews, bad review reply, repeat customers, referrals, loyalty, cancellations, support replies | retention |
| Tools, processes, suppliers, hiring, weekly routine | operations |
| Funding, grants, competitions, crowdfunding, pitch deck, investors | fundraising (+ finance) |
| Check this plan / document / number before I act | red team |
| Should I quit my job / raise money / pivot / hire? (big decision) | board meeting (red team) after the relevant departments report |

If a department the question needs wasn't part of the original build (e.g. the founder now wants TikTok content), run it in full mode first so it has its foundation files, then answer the question.

## Rules

- Re-read `00-hq/BRIEF.md`, `DECISIONS.md` and `KEY-NUMBERS.md` before routing; the business may have moved on since the last session.
- If an answer changes a key number or reverses a decision, update `00-hq/` and tell the founder what changed downstream (which department files are now stale).
- Day-to-day execution (sending invoices, chasing payments, payroll, inbox, posting) belongs to a small-business operations plugin if one is installed. Departments plan and decide; they don't execute.

## Monthly check-in

1. Ask for last month's real figures (whatever the founder has: revenue, operating expenses, net profit, ending cash, new customers) and one line on what happened.
2. Append a row to `00-hq/ACTUALS.csv` with the model month number.
3. Run `plan_vs_actual.py` and summarise: what's on track, what's off, and the one thing to change this month.
4. Two months off track in the bad direction: rerun the financial model with Finance using what's now known, and ask the owning department what to change.

## Board meeting format

Delegate to `biz-red-team` with: the exact decision, the options on the table, the files to read, and "board meeting". It returns `board-meeting.md` with 5 advisor archetypes chosen to disagree, each grounded in workspace evidence, then the disagreement, a recommendation, and the decision the founder must make. Always label it a simulation. Present it to the founder as: the decision, the strongest case on each side, the recommendation, and what would change it.
