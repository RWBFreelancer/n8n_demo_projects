# n8n access

- Instance: `N8N_BASE_URL` in `.env` (n8n Cloud).
- API: `$N8N_BASE_URL/api/v1`, header `X-N8N-API-KEY: $N8N_API_KEY`.
- API docs: https://docs.n8n.io/api/ — check before use (see `docs/docs-check.md`).

## Shared workspace (Robert Grove)
- Never use, copy, or export credentials already in it.
- Swap every credential to mine. Unsure which one: ask me.
- OAuth credentials (Google, Slack OAuth) need a browser login. Ask me to create them in the UI.

## Common calls
- `GET/POST /workflows`, `GET/PUT/DELETE /workflows/{id}`
- `POST /workflows/{id}/activate`, `/deactivate`
- `GET /credentials/schema/{type}`, `POST /credentials`
- `GET /executions?workflowId=<id>&includeData=true`
