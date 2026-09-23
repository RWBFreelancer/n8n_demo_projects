# Check official docs first

Do this before a build, and again when a node or API call fails.

1. List every app and node the workflow uses.
2. Read the current official docs for each one (WebFetch / WebSearch).
   - n8n nodes: https://docs.n8n.io/integrations/
   - n8n API: https://docs.n8n.io/api/
   - n8n release notes (breaking changes): https://docs.n8n.io/release-notes/
   - Each third-party app: its own API reference and changelog.
3. Check the node `typeVersion` against the version on my n8n instance. Use the newest version the instance supports.
4. Check for deprecated endpoints, auth methods, fields, and model names.
5. Note the doc links and versions used in `projects/<client-slug>/README.md`.

On an error: read the error, then re-check the docs for that node or endpoint before you change the workflow.
