---
name: github-accounts
description: "User's GitHub accounts — new repos go under bulzart, not bulzartaliu50-lang; gh CLI holds both"
metadata:
  node_type: memory
  type: user
  originSessionId: ad93ae0b-2399-49b3-b8da-a9d062dacd3b
  modified: 2026-11-13T17:11:25.368Z
---

The user's own repos belong on the **bulzart** GitHub account (e.g. bulzart/loupe, bulzart/ig-like-filter). When asked to "create a repo and push", create it under bulzart, private by default.

gh CLI (2026-10-21) is logged in to both `bulzart` (added via a fine-grained PAT the user supplied) and `bulzartaliu50-lang`; the active account was left as `bulzartaliu50-lang`. Use `gh auth switch -u bulzart` (or `gh repo create bulzart/<name>` after switching) and push with `git -c credential.helper= -c 'credential.helper=!gh auth git-credential' push`. Git Credential Manager also stores bulzart (used by [[loupe-web-app]] pushes).

**Why:** 2026-10-21 I created ig-like-filter on bulzartaliu50-lang and the user corrected: "not on this one, in bulzart account".
**How to apply:** default the owner to bulzart; never store or echo the token.

**Checked 2026-11-13 (supersedes the lines above where they differ):**
- `gh auth status` says not logged in to any host: there is no `%APPDATA%\GitHub CLI` folder on this PC. Git Credential Manager does hold `git:https://bulzart@github.com` and `git push --dry-run` to bulzart/claude-config authenticates (so a plain `git push` works for existing bulzart repos); an `ls-remote` proves nothing on a public repo.
- ALL THREE bulzart repos are PUBLIC (GitHub API, no login): claude-config, loupe, ig-like-filter. My earlier notes said private; so "private by default" is only my default for a NEW repo: say so, and ask before pushing personal content (memory notes) to a public repo.
- The Chrome profile the browser tools use (Browser 1) is signed in to GitHub as a THIRD account, `alternuslamiart`, with no switch to bulzart; a second Chrome ("Browser 2") is connected but I may not pick it myself (the tool says ask the user). Never create a repo there: it would land on the wrong account.
- The user said a peer session ("Qwen3 TTS 1.7B bf16 and ACE-Step 1.5") knows how it pushes to git as bulzart: ask it with SendMessage (information only).
- New extension repo: local repo C:\Users\Bulzart\Documents\twitch-chunk-recorder, branch main, commit 8f0c881 (50 files, commit identity bulzart + the GitHub no-reply address, not the gmail address); GitHub repo bulzart/twitch-chunk-recorder not created yet (see the answer of the peer session).
