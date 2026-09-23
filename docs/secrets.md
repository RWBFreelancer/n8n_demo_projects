# Secrets

- Real keys: `.env` (gitignored). Template with key names: `.env.example` (committed).
- New key needed: add the name to both files, value empty in `.env.example`. Ask me for the value.
- Never print a key, log it, put it in workflow JSON, or put it in a URL.
- Before export to `projects/<client-slug>/workflows/`, remove any secret from the JSON.
