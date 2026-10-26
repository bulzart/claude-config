## 11. Credits, licence and honesty

- Every ElevenLabs call spends the user's credits: about one credit per character of the text as sent, tags included (`eleven_v4`,
  measured 2026-10-26: 242 credits for a 240-character script). One call per script version, never a test call, at most two takes per
  script, every take recorded with `T voiceover record` so a resume finds it and never buys it again.
- **lipsync** adds one Higgsfield generation per voiced video (`sync_so`, preflighted with `get_cost` once its clip exists); **native** and
  **overlay** add none.
- The wrap-up states the method, the voice, the language, the preference, the takes, the sync passes and the credits used
  (`check_subscription` now against `voiceover.characters_left_at_start`).
- The free plan carries no commercial licence: an ad voiced on it is not posted until the account is on a paid plan; the wrap-up says so
  when `voiceover.tier` is `free`.
- Never claim that a take was listened to, or that its pronunciation, accent or dialect is right; never let the model's own voice stand in
  for the take, except the stated fallback of §8.
