# Business Starter

**A whole startup team inside Claude Code, for any kind of business.** Your main chat becomes **HQ**, the founder's chief of staff. HQ interviews you, picks the playbook for your type of business, then splits the work across up to **16 specialist department agents** that research and build in parallel, each in its own folder of a shared workspace. HQ merges what they find, keeps the numbers consistent across departments, and stops at honest go / pivot / kill gates so you don't spend months on an idea the evidence says won't work.

```
                         You (the founder)
                                |
                          HQ  (main chat)
                                |
  +-----------+--------+-----------+------------+------------+---------+---------+
 Wave 1       Gate     Wave 2      Wave 3a      Wave 3b      Wave 4    Wave 5
 Research     go/      Design      Build-out    Growth       Funding   Review
 market       pivot/   strategy    finance      content      (only if  red team
 competitors  kill     brand       legal        retention    needed)
 customers             product     marketing
                                   operations
                                   sales, commerce
```

## What you get

- **16 departments**, each a dedicated subagent with its own instructions, deliverables and report format:
  market, competitors, customers, strategy, brand, product, finance, legal and compliance, marketing, **content and social**, sales, **commerce**, **retention**, operations, fundraising, and an independent red team that checks everyone else's work.
- **Playbooks for 16 business types** so the plan fits what you're actually building: physical product brands, food and drink, local services, personal and creative services, freelance and agencies, software and apps, games, creators and media, courses and coaching, ecommerce reselling, shops and cafés, marketplaces, B2B and wholesale, events, hardware, and nonprofits. The playbook decides which departments run and what extra work each one does (food permits for a bakery, map listings and reviews for a cleaning business, store pages and wishlists for a game).
- **A content and social engine** for businesses that grow through attention: platform strategy (face or faceless), trend research in your niche, ready-to-film TikTok / Reels / Shorts scripts with hooks and shot lists, a hook bank, a 30-day calendar with batching and repurposing, a phone-only production kit, creator and UGC partnerships with proper disclosure, and a weekly numbers loop.
- **Commerce for product sellers**: where to sell (own site, marketplaces, social shops, markets, stockists, wholesale), per-unit margins on every channel after fees, shipping, returns and ads, break-even ROAS, listings, product photo brief, packaging, shipping and an inventory plan.
- **Retention**: onboarding, a support playbook, a reviews system, referral and loyalty programs, churn and win-back.
- **A shared workspace** (`business/`) where HQ owns the single source of truth: the company brief, decision log, assumption register, key numbers, open questions and your real monthly results. Close the chat, come back next week, and HQ resumes from the checkpoint.
- **Gates, not just documents.** A weighted go / pivot / kill scorecard after research, a customer-discovery checkpoint with a real interview kit, and a red-team review before launch.
- **Deterministic maths.** Market sizing, unit economics, per-channel pricing, service rates, the scorecard and a monthly financial model are Python scripts, so the numbers don't drift. The model writes a **live-formula Excel file**, low / base / high scenarios, a sensitivity table, and shows the **cash tied up in stock** for product businesses.
- **Plan vs actual.** Once you're running, log real monthly numbers and HQ shows where you're drifting from the plan and what to change.
- **Jurisdiction-aware legal research** from official sources, including labelling, food permits, selling across borders, influencer disclosure rules, and what changes if the founder is under 18.
- **Honesty built in.** Every number is sourced or logged as an assumption with a confidence level, verdicts follow evidence, and customer-facing content uses real proof: no fake reviews, bought engagement or invented urgency.

## Install

In Claude Code, add the marketplace once:

```
/plugin marketplace add HunterParass/business-starter
```

Then either install the whole toolkit in one go:

```
/plugin install business-suite@business-starter
```

or just the HQ:

```
/plugin install business-starter@business-starter
```

Restart Claude Code (or run `/reload-plugins`) and everything is available.

### What's in the marketplace

The marketplace is the "mega skill": one place to install everything worth having for a business, without stuffing it all into one skill (a skill is picked by a short description and loads its whole instruction file, so one giant skill triggers badly and bloats every task). HQ knows when to hand work to each plugin. Third-party plugins are fetched from their own repos at commits that were reviewed and test-installed, not copied into this repo.

| Plugin | In `business-suite` | What it adds | License |
|---|---|---|---|
| `business-starter` | yes | The HQ skill and 16 department agents | MIT |
| `docx`, `xlsx`, `pptx`, `pdf` | yes | Anthropic's document skills, so HQ can hand you proposals, contracts and one-pagers as Word or PDF, decks as PowerPoint, trackers as Excel. Only these four from [anthropics/skills](https://github.com/anthropics/skills); the rest of that repo (art, Slack GIFs, Anthropic's own brand guidelines) isn't useful for your business | Apache-2.0 |
| `context7` | yes | [Upstash Context7](https://github.com/upstash/context7): current docs for libraries and platforms (Shopify themes, Stripe, site frameworks) whenever code gets written. A hosted MCP server; your library questions go to context7.com | MIT |
| `superpowers` | no, optional | [obra/superpowers](https://github.com/obra/superpowers): plan-first, test-driven coding workflow. It adds a "use skills before anything" rule to every session, so install it in coding projects only (`--scope project`) | MIT |
| `small-business` | no, optional | Anthropic's [operations skills](https://github.com/anthropics/knowledge-work-plugins) for once you're running: invoices, bills, cash flow, payroll prep, inbox, reviews, posting. HQ's Operate mode routes day-to-day tasks to it | Apache-2.0 |

Not included, on purpose:
- **claude-mem**: a background worker and local database that records your sessions. HQ's `00-hq/` files already carry the business from session to session, and Claude Code has its own memory. Install it yourself if you want it.
- **Most of [awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)**: the business skills there are short prompts with no tools behind them (the domain brainstormer claims to check availability but can't; the ads extractor claims to scrape ad libraries with no browser), and the rest is developer tooling. Their two good ideas are rebuilt properly here: `domain_check.py` asks the domain registries directly, and the ad library scan uses a real browser or says it didn't look.

**Manual install** (no plugin system):

```bash
git clone https://github.com/HunterParass/business-starter
cp -r business-starter/skills/business-hq ~/.claude/skills/
cp business-starter/agents/*.md ~/.claude/agents/
```

Requires Python 3.9+. `openpyxl` is optional (`pip install openpyxl`); without it the model writes CSV and Markdown but no `.xlsx`.

## Use it

Just describe what you want. The skill triggers on things like:

- "I want to start a candle business and sell on TikTok. Is it worth doing?"
- "I have an idea for a meal-prep service for night-shift nurses"
- "I want to start something with AI where I live, but I don't have an idea yet. I have 2 hours a day and $5k"
- "Help me start a lawn care business in my neighbourhood this summer"
- "Give me a month of TikTok scripts for my crochet shop"
- "Build me a full business plan for an indie mobile game studio"
- "Here are last month's numbers, are we on track?"
- "Board meeting: should I quit my job to do this full time?"

Or call it directly with `/business-starter:business-hq`.

### Modes

| Mode | What happens | Cost |
|---|---|---|
| **Idea scan** | No idea yet? 3 departments hunt for real problems (local businesses, people and groups, services proven elsewhere), then every idea is ranked on the founder lens: idiot index (ease x money), first-quarter income and clients against your real hours, stickiness, and how much AI can do. Top ideas get the scorecard | low-medium |
| **Quick scan** | 3 research departments, then the scorecard and a one-page verdict | low |
| **Full build** | Every department your playbook needs, in waves with gates, ending in an executive summary and a this-week / 30 / 60 / 90-day launch plan | high |
| **Single department** | One deliverable, e.g. a month of video scripts, pricing, or a financial model | low |
| **Operate** | Business already running; HQ routes your questions and runs monthly plan-vs-actual check-ins | per question |
| **Board meeting** | A labelled simulation of 5 advisor archetypes who disagree, on one decision | low |

**Start with Quick scan.** A full build runs a lot of agents doing web research and uses a lot of your plan's usage. Most ideas should earn the full build by passing the scorecard first.

## The workspace

```
business/
  00-hq/            BRIEF, PROGRESS, DECISIONS, ASSUMPTIONS, OPEN-QUESTIONS, KEY-NUMBERS, ACTUALS.csv (HQ only)
  01-market/        sizing, trends, demand signals
  02-competitors/   competitor matrix, pricing landscape, review mining, wedge, graveyard
  03-customers/     personas, pain evidence, interview kit, commitment tests, interview synthesis
  04-strategy/      strategy on a page, lean canvas, business model, offer, pricing, unit economics, risks
  05-brand/         positioning, messaging, naming, brand guidelines
  06-product/       MVP scope, validation experiments, build plan, product brief, roadmap
  07-finance/       startup budget, model.xlsx, scenarios, sensitivity, metrics, monthly check-in, money setup
  08-legal/         structure and registration, IP, contracts kit, compliance and risk
  09-marketing/     GTM plan, first 100 customers, launch, landing page, email, tracking, lead magnet, local presence
  10-content/       content strategy, trend research, video scripts, hook bank, calendar, production kit, creators, community
  11-sales/         playbook, outreach, discovery call, objections, partnerships, proposal template, CRM
  12-commerce/      channel plan, per-unit margins, listings, photo brief, fulfilment and shipping, inventory, wholesale
  13-retention/     customer journey, onboarding, support, reviews, loyalty and referrals, churn and win-back
  14-operations/    tool stack, processes, suppliers, team and hiring, operating rhythm, document kit
  15-fundraising/   funding options, raise or not, pitch deck outline, scripts, IC simulation
  16-review/        red-team review, board meetings
  EXECUTIVE-SUMMARY.md
  LAUNCH-PLAN.md
```

## How the orchestration works

- Subagents start with no memory of your chat, so HQ writes each one a full delegation message (workspace paths, playbook, mode, jurisdiction, your constraints, what to read, what to produce, and anything you said that isn't in the files yet).
- Departments in the same wave run **concurrently** and never depend on each other; anything dependent waits for the next wave.
- Subagents can't ask you questions, so they log them with a default and keep working. HQ batches the important ones to you, at most four at a time.
- Only HQ writes to `00-hq/`, so parallel agents never overwrite each other. Departments *propose* assumptions and numbers; HQ records them and resolves conflicts.
- Departments don't have the tool to spawn their own subagents, which keeps costs predictable.
- Nothing is sent, posted, listed, bought, registered, signed or paid by any agent. Everything is a draft until you act on it.

## Scripts

All in `skills/business-hq/scripts/`, each with `--help`:

| Script | Does |
|---|---|
| `init_workspace.py` | Creates the workspace; never overwrites; `--check` shows status |
| `scorecard.py` | 9-dimension weighted go / pivot / kill verdict with evidence-strength rules |
| `market_size.py` | Bottom-up TAM / SAM / SOM with top-down cross-check and capacity check |
| `unit_economics.py` | LTV, CAC, LTV:CAC, payback for subscription or transactional models |
| `pricing_calc.py` | `product`: what you keep per unit on every sales channel, break-even ROAS, price for a target margin. `service`: hourly, day and package rate from an income target |
| `financial_model.py` | Monthly driver-based model: live-formula `.xlsx`, CSV, scenarios, `--sensitivity`, streams that start later, stock bought ahead of sales |
| `plan_vs_actual.py` | Real monthly results vs the plan, with drift flags |
| `domain_check.py` | Asks each domain registry (RDAP) whether names are registered, across the TLDs you choose, with name-quality flags and the trademark and business-name checks still to do |
| `idea_lens.py` | Founder lens for ranking ideas: idiot index quadrant, simulated first-quarter revenue and clients capped by your weekly hours, stickiness, AI share; `--same-ramp` compares ideas on equal client ramps |

Run the tests with `python3 -m unittest discover tests -v`. If LibreOffice is installed, the suite also recalculates the generated spreadsheets and checks every cell against the Python calculation.

## Limits, honestly

- It's research and planning, **not legal, tax or financial advice**. Legal and finance departments tell you when you need a professional.
- Agents can be wrong. Sources are dated and the red team re-checks the important ones, but verify anything you're about to pay for, sign or file. Platform fees, rules and trends change fast.
- The financial model is deliberately simple (flat tax on positive profit, no sales tax, customers pay when they buy). Fine for planning, not for your accountant. B2B businesses with payment terms should adjust for the wait.
- Content plans don't make videos go viral. They make it much more likely you post consistently, learn from the numbers and keep improving.
- Customer discovery is your job. No amount of desk research replaces ten real conversations, and HQ will keep telling you that.

## Credits

Built on ideas from the best open-source founder, marketing and business skill packs. See [CREDITS.md](CREDITS.md).

## License

MIT
