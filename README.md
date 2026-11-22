# Business Starter

**A whole startup team inside Claude Code.** Your main chat becomes **HQ**, the founder's chief of staff. HQ interviews you, then splits the work across **13 specialist department agents** that research and build in parallel, each in its own folder of a shared workspace. HQ merges what they find, keeps the numbers consistent across departments, and stops at honest go / pivot / kill gates so you don't spend months on an idea the evidence says won't work.

```
                     You (the founder)
                            |
                      HQ  (main chat)
                            |
   +------------+-----------+------------+-------------+-----------+
 Wave 1        Gate        Wave 2       Wave 3        Wave 4      Wave 5
 Research      go/pivot/   Design       Build-out     Funding     Review
 market        kill        strategy     finance       (only if    red team
 competitors   scorecard   brand        legal         needed)
 customers                 product      marketing
                                        sales, ops
```

## What you get

- **13 departments**, each a dedicated subagent with its own instructions, deliverables and report format:
  market, competitors, customers, strategy, brand, product, finance, legal and compliance, marketing, sales, operations, fundraising, and an independent red team that checks everyone else's work.
- **A shared workspace** (`business/`) where every department writes to its own folder and HQ owns the single source of truth: the company brief, decision log, assumption register, key numbers and open questions. Close the chat, come back next week, and HQ resumes from the checkpoint.
- **Gates, not just documents.** A weighted go / pivot / kill scorecard after research, a customer-discovery checkpoint with a real interview kit, and a red-team review before launch.
- **Deterministic maths.** Market sizing, unit economics, the scorecard and a 36-month financial model are Python scripts, so the numbers don't drift. The model writes a **live-formula Excel file** (change a blue input, everything updates), a CSV, low / base / high scenarios and a sensitivity table showing which assumptions actually matter.
- **Jurisdiction-aware legal research** from official government sources: structure options, registration, tax registration thresholds, licences, trademarks, privacy and anti-spam rules, platform rules, and clear "talk to a professional now" triggers. Includes what changes if the founder is under 18.
- **Concrete go-to-market**: Bullseye channel tests with pass thresholds, a named first-100-customers plan, launch plan, landing page copy, email sequences, sales scripts, proposal template, and a starter document kit (invoice, quote, receipt, expense log, weekly report).
- **Honesty built in.** Every number is sourced or logged as an assumption with a confidence level, and the verdict follows the evidence, not your excitement.

## Install

In Claude Code:

```
/plugin marketplace add HunterParass/business-starter
/plugin install business-starter@business-starter
```

Restart Claude Code and the skill and agents are available.

**Manual install** (no plugin system):

```bash
git clone https://github.com/HunterParass/business-starter
cp -r business-starter/skills/business-hq ~/.claude/skills/
cp business-starter/agents/*.md ~/.claude/agents/
```

Requires Python 3.9+. `openpyxl` is optional (`pip install openpyxl`); without it the model writes CSV and Markdown but no `.xlsx`.

## Use it

Just describe what you want. The skill triggers on things like:

- "I have an idea for a meal-prep service for night-shift nurses. Is it worth doing?"
- "Help me start a business selling custom phone cases"
- "Build me a full business plan for an indie mobile game studio"
- "Just do the legal setup for my freelance design business in Ontario"
- "Board meeting: should I quit my job to do this full time?"

Or call it directly with `/business-starter:business-hq`.

### Modes

| Mode | What happens | Cost |
|---|---|---|
| **Quick scan** | 3 research departments, then the scorecard and a one-page verdict | low |
| **Full build** | Every department the business needs, in waves with gates, ending in an executive summary and a this-week / 30 / 60 / 90-day launch plan | high |
| **Single department** | One deliverable, e.g. pricing or a financial model | low |
| **Operate** | Business already running; HQ routes your questions to the right departments | per question |
| **Board meeting** | A labelled simulation of 5 advisor archetypes who disagree, on one decision | low |

**Start with Quick scan.** A full build runs a lot of agents doing web research and uses a lot of your plan's usage. Most ideas should earn the full build by passing the scorecard first.

## The workspace

```
business/
  00-hq/            BRIEF, PROGRESS, DECISIONS, ASSUMPTIONS, OPEN-QUESTIONS, KEY-NUMBERS (HQ only)
  01-market/        sizing, trends, demand signals
  02-competitors/   competitor matrix, pricing landscape, review mining, wedge, graveyard
  03-customers/     personas, pain evidence, interview kit, commitment tests, interview synthesis
  04-strategy/      strategy on a page, lean canvas, business model, pricing, unit economics, risks
  05-brand/         positioning, messaging, naming, brand guidelines
  06-product/       MVP scope, validation experiments, build plan, product brief, roadmap
  07-finance/       startup budget, model.xlsx, scenarios, sensitivity, metrics, money setup
  08-legal/         structure and registration, IP, contracts kit, compliance and risk
  09-marketing/     GTM plan, first 100 customers, launch, landing page, content, email
  10-sales/         playbook, outreach, discovery call, objections, proposal template, CRM
  11-operations/    tool stack, processes, suppliers, team plan, operating rhythm, document kit
  12-fundraising/   funding options, raise or not, pitch deck outline, scripts, IC simulation
  13-review/        red-team review, board meetings
  EXECUTIVE-SUMMARY.md
  LAUNCH-PLAN.md
```

## How the orchestration works

- Subagents start with no memory of your chat, so HQ writes each one a full delegation message (workspace paths, mode, jurisdiction, what to read, what to produce, and anything you said that isn't in the files yet).
- Departments in the same wave run **concurrently** and never depend on each other; anything dependent waits for the next wave.
- Subagents can't ask you questions, so they log them with a default and keep working. HQ batches the important ones to you, at most four at a time.
- Only HQ writes to `00-hq/`, so parallel agents never overwrite each other. Departments *propose* assumptions and numbers; HQ records them and resolves conflicts.
- Departments don't have the tool to spawn their own subagents, which keeps costs predictable.
- Nothing is sent, posted, bought, registered, signed or paid by any agent. Everything is a draft until you act on it.

## Scripts

All in `skills/business-hq/scripts/`, each with `--help`:

| Script | Does |
|---|---|
| `init_workspace.py` | Creates the workspace; never overwrites; `--check` shows status |
| `scorecard.py` | 9-dimension weighted go / pivot / kill verdict with evidence-strength rules |
| `market_size.py` | Bottom-up TAM / SAM / SOM with top-down cross-check and capacity check |
| `unit_economics.py` | LTV, CAC, LTV:CAC, payback for subscription or transactional models |
| `financial_model.py` | 36-month driver-based model: live-formula `.xlsx`, CSV, scenarios, `--sensitivity` |

Run the tests with `python3 -m unittest discover tests -v`. If LibreOffice is installed, the suite also recalculates the generated spreadsheet and checks every cell against the Python calculation.

## Limits, honestly

- It's research and planning, **not legal, tax or financial advice**. Legal and finance departments tell you when you need a professional.
- Agents can be wrong. Sources are dated and the red team re-checks the important ones, but verify anything you're about to pay for, sign or file.
- The financial model is deliberately simple (flat tax on positive profit, no sales tax or payment timing). Fine for planning, not for your accountant.
- Customer discovery is your job. No amount of desk research replaces ten real conversations, and HQ will keep telling you that.

## Credits

Built on ideas from the best open-source founder and business skill packs. See [CREDITS.md](CREDITS.md).

## License

MIT
