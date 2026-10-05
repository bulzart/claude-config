# Validation Record

Package: Seedance 2.5 Director, revision 2.1.0. Validation date: 2026-09-17.

## Checks performed for this delivery

| Check | Result and scope |
|---|---|
| Prior archive intake | One skill entrypoint; safe extraction paths; original archive CRC passed |
| Skill-creator validator | Passed frontmatter and skill naming checks |
| Interface metadata | Parsed YAML; required display fields present |
| Local package validator | Passed required-file, single-entrypoint, frontmatter-subset, local-link, anchor, code-fence, JSON-fixture, and package-size checks |
| Python unit tests | All 10 tests passed: clean package; missing file; broken link; broken anchor; path escape; malformed JSON; duplicate case ID; extra skill entrypoint; unclosed fence; hash tampering |
| Evaluation fixtures | 46 unique cases with required fields; six contain concrete multi-turn conversation fixtures |
| File manifest | SHA-256 hashes recorded for every distributed file except the manifest itself; integrity check passed |
| Final archive | Repackaged through the skill-creator packaging script; CRC, one skill root, size, and extracted-file integrity checked |

The local validator is read-only and uses no network, model calls, or paid services. Its metadata checks intentionally cover a small documented subset, not arbitrary YAML semantics. The separate skill-creator validator and YAML parser were also used during preparation.

## Not performed or established

The 46 downstream-agent behavioral cases were not executed against the user's agent. No example was rendered or benchmarked in Seedance. No model-internal implementation, measured reliability gain, flawless physics, perfect continuity, or provider eligibility was certified. External sources were inherited from the prior guide and were not newly fetched in this packaging revision. No skill was installed into the user's environment, and no permissions, account-wide memory, or provider connection were granted.

## What to verify after installation

Run representative multi-turn cases against the actual host, inspect its final prompts, and record pass/fail/unknown per expected behavior. Only render with authorization; inspect complete temporal behavior and audio. Re-run file-integrity checks after transfer. After authorized edits, regenerate the reading edition and manifest before treating the old hashes as current.
