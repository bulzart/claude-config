## 7. Fixed output: vertical 9:16 at 720p

Every generation in both modes is 9:16 at 720p. It is never asked. `models/index.json →
output_9x16_720p` holds the exact per-model parameters. Rules:

1. **Native models.** Send `aspect_ratio:"9:16"` plus the model's 720p setting: `resolution:"720p"`,
   `quality:"720p"` (Wan 2.6), or `mode:"std"` (Kling 3.0 / Cinema Studio Video 2, [INFERRED]
   standard tier = 720p). Seedance 2.0 at 9:16 / 720p stored `width 720, height 1280` [VERIFIED].
2. **Models without a 720p option.** Minimax Hailuo 768 / 1080, MiniMax H3 2K, H3 Max 768p, and the
   Veo tiers are generated at the closest tier. Then `atp.py conform` downscales to 720×1280:
   scale-to-cover plus a crop of a few pixels, never a stretch.
3. **Aspect follows an input.** Start-frame-locked models and edit models inherit the input's aspect.
   - Supply a 9:16 start frame, generated or prepared at 720×1280.
   - Or bring the source video to 9:16 **before** editing:
     - `atp.py conform --focus-x/--focus-y` when a crop keeps every important subject; the tool
       refuses to crop more than 12% unless told to;
     - otherwise Higgsfield `reframe` (AI expansion to 9:16, 720p, `get_cost` supported);
     - otherwise regenerate with the source as a video reference.
4. **Verify.** `atp.py qc --expect-size 720x1280` on every final. Never deliver a stretched or
   letterboxed result unless the user explicitly asked for padding (`conform --mode pad`).
5. **Stored `width`/`height` in generation params are not the output size.** A `wan3_0_prime` job at
   9:16 / 480p stored `768×1344`, but the delivered file measured **480×854 at 30 fps** [VERIFIED
   2026-09-30]. Seedance 2.0 at 9:16 / 720p stored and delivered 720×1280 [VERIFIED]. Always measure
   the downloaded file (`hf-get` reports the dimensions).

