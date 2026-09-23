# Workflow build process

## 1. Intake questions (ask all that are not answered)
- Client name and slug (for folder names)
- Goal: what problem does the demo solve? What does "success" look like?
- Trigger: webhook, form, schedule, email, chat, manual?
- Inputs: data source, sample data, format
- Outputs: where results go (Sheet, email, Slack, CRM, etc.)
- Apps and accounts: which tools, and which of MY credentials to use
- AI: model and provider, prompt style, output format
- Volume and timing: how many items, how often
- Errors: what happens on failure (retry, alert, log)?
- Demo needs: fake or real data? Loom video? Screenshots?
- Paid or unpaid? Deadline?
- Anything the client said they must see

When the slug is known, create `projects/<client-slug>/` and save the brief in its `README.md`.

## 2. Check docs
Follow `docs/docs-check.md` for every app and node in the plan.

## 3. Three routes
For each route give: nodes/apps used, cost, build time, risk, demo impact.
Then say: "I pick route X because ...". Wait for my choice.

## 4. Credentials (shared workspace)
See `docs/n8n-access.md`.
1. List every credential the workflow uses (`GET /api/v1/credentials` or the JSON `credentials` fields).
2. Map each one to my credential. Ask me when unsure.
3. Create missing ones from `.env` values via `POST /api/v1/credentials`, or ask me to create OAuth ones in the UI (Google, Slack OAuth need a browser login).
4. Never copy, export, or reuse the workspace owner's credentials.

## 5. Test checklist
- On any error: re-check the docs first (`docs/docs-check.md`).
- Logic: trace sample data through each node. Check expressions, field names, IF/Switch branches, empty inputs.
- Import: `POST /api/v1/workflows` (strip `id`, `active`, `tags` if the API rejects them).
- Run: trigger via test webhook or manual run. Read results with `GET /api/v1/executions?workflowId=<id>&includeData=true`.
- Record pass/fail in `projects/<client-slug>/README.md`.
- Export the final JSON to `projects/<client-slug>/workflows/`. Remove any secrets first.
