---
name: github-accounts
description: "User's GitHub accounts — new repos go under bulzart, not bulzartaliu50-lang; gh CLI holds both"
metadata:
  node_type: memory
  type: user
  originSessionId: ad93ae0b-2399-49b3-b8da-a9d062dacd3b
  modified: 2026-10-21T18:19:25.892Z
---

The user's own repos belong on the **bulzart** GitHub account (e.g. bulzart/loupe, bulzart/ig-like-filter). When asked to "create a repo and push", create it under bulzart, private by default.

gh CLI (2026-10-21) is logged in to both `bulzart` (added via a fine-grained PAT the user supplied) and `bulzartaliu50-lang`; the active account was left as `bulzartaliu50-lang`. Use `gh auth switch -u bulzart` (or `gh repo create bulzart/<name>` after switching) and push with `git -c credential.helper= -c 'credential.helper=!gh auth git-credential' push`. Git Credential Manager also stores bulzart (used by [[loupe-web-app]] pushes).

**Why:** 2026-10-21 I created ig-like-filter on bulzartaliu50-lang and the user corrected: "not on this one, in bulzart account".
**How to apply:** default the owner to bulzart; never store or echo the token.
