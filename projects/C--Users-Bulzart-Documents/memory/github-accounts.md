---
name: github-accounts
description: "User's GitHub accounts — new repos go under bulzart, not bulzartaliu50-lang; gh CLI holds both"
metadata:
  node_type: memory
  type: user
  originSessionId: ad93ae0b-2399-49b3-b8da-a9d062dacd3b
  modified: 2026-11-13T18:02:59.348Z
---

The user's own repos belong on the **bulzart** GitHub account (e.g. bulzart/loupe, bulzart/ig-like-filter). When asked to "create a repo and push", create it under bulzart, private by default.

gh CLI (2026-10-21) is logged in to both `bulzart` (added via a fine-grained PAT the user supplied) and `bulzartaliu50-lang`; the active account was left as `bulzartaliu50-lang`. Use `gh auth switch -u bulzart` (or `gh repo create bulzart/<name>` after switching) and push with `git -c credential.helper= -c 'credential.helper=!gh auth git-credential' push`. Git Credential Manager also stores bulzart (used by [[loupe-web-app]] pushes).

**Why:** 2026-10-21 I created ig-like-filter on bulzartaliu50-lang and the user corrected: "not on this one, in bulzart account".
**How to apply:** default the owner to bulzart; never store or echo the token.

**Checked 2026-11-13 (supersedes the lines above where they differ):**
- `gh auth status` says not logged in to any host: there is no `%APPDATA%\GitHub CLI` folder on this PC. Git Credential Manager does hold `git:https://bulzart@github.com` and `git push --dry-run` to bulzart/claude-config authenticates (so a plain `git push` works for existing bulzart repos); an `ls-remote` proves nothing on a public repo.
- ALL THREE bulzart repos are PUBLIC (GitHub API, no login): claude-config, loupe, ig-like-filter. My earlier notes said private; so "private by default" is only my default for a NEW repo: say so, and ask before pushing personal content (memory notes) to a public repo.
- The Chrome profile the browser tools use (Browser 1) is signed in to GitHub as a THIRD account, `alternuslamiart`, with no switch to bulzart; a second Chrome ("Browser 2") is connected but I may not pick it myself (the tool says ask the user). Never create a repo there: it would land on the wrong account.
- The user said a peer session ("Qwen3 TTS 1.7B bf16 and ACE-Step 1.5") knows how it pushes to git as bulzart: ask it with SendMessage (information only). ANSWER (2026-11-13, checked against this repo's reflog: pushes of origin/pc on 11-05, 11-06, 11-07, 11-09, 11-11 and 11-13 15:24): a plain `git push origin pc` in C:\Users\Bulzart\.claude works with no flags and no token on the command line; the remote URL keeps the user name (https://bulzart@github.com/bulzart/claude-config.git) so Git Credential Manager answers from `git:https://bulzart@github.com`; keep `bulzart@` in the URL of any new remote. Nobody has a verified way to CREATE a repo (gh has no login). I decided NOT to pull the token out of the credential store for a REST call (that is handling the user's login token myself): the user creates the empty repo, or runs `! gh auth login --hostname github.com --git-protocol https --web` as bulzart.
- The user's own ~/.claude/VERSIONING.md (line 22) says the claude-config remote is PRIVATE; GitHub says public. So the user probably believes it is private: never push to it without saying so first. 13 commits (including memory notes that name the third account) stay local until the user answers.
- New extension repo: local repo C:\Users\Bulzart\Documents\twitch-chunk-recorder, branch main, commit 8f0c881 (50 files, commit identity bulzart + the GitHub no-reply address, not the gmail address); the user created the empty PRIVATE repo bulzart/twitch-chunk-recorder himself on 2026-11-13 (that was the way: nobody can create a repo from here), and I pushed `main` with a plain `git push -u origin main` (remote URL https://bulzart@github.com/bulzart/twitch-chunk-recorder.git); remote main = 8f0c881, still private (404 without a login). Later pushes there are plain `git push`.
