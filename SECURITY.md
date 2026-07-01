# Security

## Supported Versions

ZTube does not have stable release versions yet. Report security issues against
the current main branch unless a release branch is created later.

## Reporting A Vulnerability

Do not open a public issue for secrets, credential leaks, or exploitable
security problems. Contact the maintainer privately, or open a minimal public
issue asking for a secure contact path without including sensitive details.

## Secrets

Never commit:

- `.env` files with real values.
- `api_key.txt` or other local secret files.
- YouTube Data API keys.
- `YOUTUBE_VISITOR_DATA`.
- `YOUTUBE_PO_TOKEN`.
- OAuth cache/token files.
- Local settings containing private paths or credentials.

If a key is committed, pushed, shared, logged, or included in a screenshot,
revoke it in the provider dashboard. Removing it from git history is not enough
once it has been exposed.

## Desktop App

The desktop app reads secrets from environment variables or local `.env` files.
The repository ignores those local files, and docs/examples must only contain
placeholder values.

## Future Web App

Any future web app must keep private keys server-side only. Do not expose API
keys in browser JavaScript, public environment variables, client bundles, logs,
screenshots, downloadable artifacts, or error payloads.
