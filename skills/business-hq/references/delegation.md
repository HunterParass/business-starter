# Delegating to a department

Subagents start with **no memory of the conversation**. A department only knows what's in its own definition, your delegation message, and the files you tell it to read. A thin delegation produces generic work.

## Template

Fill every line. Use absolute paths.

```
You are being run by Business HQ as the <DEPARTMENT> department.

WORKSPACE: <abs path>/business
YOUR FOLDER: <abs path>/business/<NN-folder>/   (write only here)
SCRIPTS: <SKILL_DIR abs path>/scripts   (python3 <script> --help)
FRAMEWORKS: <SKILL_DIR abs path>/references/frameworks.md
PLAYBOOKS: <SKILL_DIR abs path>/references/playbooks.md
PLAYBOOK: <number and name of primary type> (+ <secondary>, if any)
MODE: quick | full
TODAY: <YYYY-MM-DD>
JURISDICTION: <country, province/state>    CURRENCY: <code>
BUSINESS TYPE: <type>    CUSTOMER TYPE: <consumers | businesses>
FOUNDER CONSTRAINTS: <budget, hours/week, age bracket if relevant, on camera or not, hard no's>

READ FIRST:
- 00-hq/BRIEF.md, 00-hq/DECISIONS.md, 00-hq/ASSUMPTIONS.md, 00-hq/KEY-NUMBERS.md
- <upstream files for this wave, see below>

TASK:
<Default: your full deliverable list for this mode, plus the extra items the playbook lists for you.
 Or name specific deliverables, a revision ("fix X in pricing.md because Y"), or a question.>

WHAT HQ KNOWS THAT ISN'T IN THE FILES YET:
<recent founder answers, decisions made in chat, preferences>

DEFAULTS FOR OPEN QUESTIONS:
<question -> default to use>

Return your standard report block when done.
```

## Upstream files by wave

| Wave | Department | Also read |
|---|---|---|
| 1 Research | market, competitors, customers | brief only (they run in parallel) |
| 2 Design | strategist | `01-market/`, `02-competitors/`, `03-customers/` |
| 2 Design | brand | `02-competitors/competitors.md`, `03-customers/personas.md`, `pain-evidence.md` |
| 2 Design | product | `03-customers/`, `02-competitors/gaps-and-wedge.md`, `00-hq/scorecard.json` |
| 3a Build-out | finance | `04-strategy/`, `06-product/build-plan.md`, KEY-NUMBERS |
| 3a Build-out | legal | `06-product/` (platform, safety), `04-strategy/business-model.md` |
| 3a Build-out | marketing | `05-brand/`, `03-customers/personas.md`, `04-strategy/pricing.md`, `04-strategy/offer.md` |
| 3a Build-out | sales | `05-brand/messaging.md`, `03-customers/`, `04-strategy/pricing.md`, `04-strategy/offer.md` |
| 3a Build-out | commerce | `04-strategy/pricing.md`, `06-product/build-plan.md`, `05-brand/positioning.md`, `03-customers/personas.md` |
| 3a Build-out | operations | `06-product/build-plan.md`, `04-strategy/business-model.md` |
| 3b Growth | content | `05-brand/`, `03-customers/personas.md`, `pain-evidence.md`, `09-marketing/gtm-plan.md`, `12-commerce/channel-plan.md` (if it exists) |
| 3b Growth | retention | `04-strategy/`, `09-marketing/`, `12-commerce/fulfilment-and-shipping.md` (if it exists), `08-legal/contracts-kit.md` |
| 4 Funding | fundraising | `07-finance/`, `01-market/`, `05-brand/positioning.md`, `00-hq/scorecard.json` |
| 5 Review | red team | the whole workspace |

Wave 3a departments run in parallel, so Finance can't read Marketing's budget or Commerce's stock plan in the same wave. Put the marketing budget, CAC target and focus channels in KEY-NUMBERS before launching Wave 3a and tell everyone to use them. If Marketing or Commerce comes back needing different figures (or a stock purchase plan), rerun Finance with them after Wave 3b.

## Launching

- One message, one Agent call per department in the wave, so they run concurrently.
- `description`: short, e.g. "Market research wave 1".
- Quick mode: say `MODE: quick` and the department trims itself to its quick deliverables.
- Don't let departments spawn their own subagents. They don't have the Agent tool, on purpose.

## After the wave

See SKILL.md Step 2.3. The short version: read reports, merge assumptions, key numbers and questions into `00-hq/`, update PROGRESS, tell the founder in under 200 words.
