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

## 2. Three routes
For each route give: nodes/apps used, cost, build time, risk, demo impact.
Then say: "I pick route X because ...". Wait for my choice.

## 3. Credentials (shared workspace)
1. List every credential the workflow uses (`GET /api/v1/credentials` or the JSON `credentials` fields).
2. Map each one to my credential. Ask me when unsure.
3. Create missing ones from `.env` values via `POST /api/v1/credentials`, or ask me to create OAuth ones in the UI (Google, Slack OAuth need a browser login).
4. Never copy, export, or reuse the workspace owner's credentials.

## 4. Test checklist
- Logic: trace sample data through each node. Check expressions, field names, IF/Switch branches, empty inputs.
- Import: `POST /api/v1/workflows` (strip `id`, `active`, `tags` if the API rejects them).
- Run: trigger via test webhook or manual run. Read results with `GET /api/v1/executions?workflowId=<id>&includeData=true`.
- Record pass/fail in `docs/<client-slug>.md`.
- Export the final JSON to `workflows/<client-slug>/`. Remove any secrets first.

## n8n API quick ref
Base: `$N8N_BASE_URL/api/v1`, header `X-N8N-API-KEY: $N8N_API_KEY`
- `GET/POST /workflows`, `GET/PUT/DELETE /workflows/{id}`
- `POST /workflows/{id}/activate`, `/deactivate`
- `GET /credentials/schema/{type}`, `POST /credentials`
- `GET /executions`, `GET /executions/{id}`
