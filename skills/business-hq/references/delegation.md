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
MODE: quick | full
TODAY: <YYYY-MM-DD>
JURISDICTION: <country, province/state>    CURRENCY: <code>
BUSINESS TYPE: <type>    CUSTOMER TYPE: <consumers | businesses>

READ FIRST:
- 00-hq/BRIEF.md, 00-hq/DECISIONS.md, 00-hq/ASSUMPTIONS.md, 00-hq/KEY-NUMBERS.md
- <upstream files for this wave, see below>

TASK:
<Default: your full deliverable list for this mode.
 Or name specific deliverables, a revision ("fix X in pricing.md because Y"), or a question.>

WHAT HQ KNOWS THAT ISN'T IN THE FILES YET:
<recent founder answers, decisions made in chat, constraints, preferences>

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
| 3 Build-out | finance | `04-strategy/`, `06-product/build-plan.md`, KEY-NUMBERS |
| 3 Build-out | legal | `06-product/` (platform, safety), `04-strategy/business-model.md` |
| 3 Build-out | marketing | `05-brand/`, `03-customers/personas.md`, `04-strategy/pricing.md` |
| 3 Build-out | sales | `05-brand/messaging.md`, `03-customers/`, `04-strategy/pricing.md` |
| 3 Build-out | operations | `06-product/build-plan.md`, `04-strategy/business-model.md` |
| 4 Funding | fundraising | `07-finance/`, `01-market/`, `05-brand/positioning.md`, `00-hq/scorecard.json` |
| 5 Review | red team | the whole workspace |

Wave 3 departments run in parallel, so Finance can't read Marketing's budget in the same wave. Put the marketing budget and CAC in KEY-NUMBERS before launching Wave 3, and tell both to use it.

## Launching

- One message, one Agent call per department in the wave, so they run concurrently.
- `description`: short, e.g. "Market research wave 1".
- Quick mode: say `MODE: quick` and the department trims itself to its quick deliverables.
- Don't let departments spawn their own subagents. They don't have the Agent tool, on purpose.

## After the wave

See SKILL.md Step 2.3. The short version: read reports, merge assumptions, key numbers and questions into `00-hq/`, update PROGRESS, tell the founder in under 200 words.
