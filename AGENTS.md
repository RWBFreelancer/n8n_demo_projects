# n8n Demo Projects

n8n demo workflows for client job applications (automation specialist).

## Always
- Never print, commit, or hardcode a secret. Keys live in `.env` only. Missing key: ask me.
- Check the app's current official docs before you build or debug. No deprecated nodes or API calls.
- Report in ASD-STE100 plain English.
- Commit when a change is done.

## Read when needed
| Task | File |
|---|---|
| New workflow or brief | `docs/workflow-process.md` |
| Check app docs / API versions | `docs/docs-check.md` |
| n8n API, shared workspace, credentials | `docs/n8n-access.md` |
| Secrets, `.env` keys | `docs/secrets.md` |
| Git, push, large files | `docs/git.md` |
| Reports, client emails, prompts, notes | `docs/writing-style.md` |

## Folders
- `workflows/<client-slug>/` — workflow JSON
- `docs/<client-slug>.md` — brief, chosen route, test results
