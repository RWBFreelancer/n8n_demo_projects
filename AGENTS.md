# n8n Demo Projects

Demo n8n workflows I build for client job applications (automation specialist role).
Paid or unpaid trials. The demo must run and look clean.

## Layout
- `workflows/<client-slug>/` — n8n workflow JSON exports
- `docs/<client-slug>.md` — client brief, chosen route, test results
- `docs/workflow-process.md` — full build process. Read it before any new workflow.

## Build process (every new workflow)
1. Read the brief. Ask me ALL missing requirements before you build. Briefs are often incomplete.
2. Give me 3 routes. Say which one you pick and why. Wait for my choice.
3. Build. Use MY credentials only (see below).
4. Test by logic first. Then import and run through the n8n API if possible.
5. Report what passed, what failed, and what I must do by hand.

## n8n access
- Instance: `N8N_BASE_URL` in `.env`. API key: `N8N_API_KEY`, header `X-N8N-API-KEY`.
- Shared workspace (Robert Grove): never use credentials already in it.
  Swap every credential to mine. If you do not know which one to use, ask me.

## Secrets
- Keys live in `.env` only (gitignored). Template: `.env.example`.
- Never print, log, commit, or hardcode a key in workflow JSON.
- If a key is missing or empty, ask me. Do not search for one.

## Git
- Commit when you finish a change. Short, plain message.
- Push to `origin` when a remote exists. If push fails, `git pull --rebase`, then push.
- Nothing over 50 MB. Large assets go to `C:\GoogleDrive\ClaudeAssets\clients\<client>\`.

## Reporting
- ASD-STE100 plain English. Short sentences. Active voice. Exact paths and commands.
