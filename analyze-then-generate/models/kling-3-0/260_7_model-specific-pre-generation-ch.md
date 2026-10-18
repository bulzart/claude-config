## 7. Model-specific pre-generation checklist

- [ ] Right id: `kling3_0` (frames, Elements, `sound`) vs `kling3_0_turbo` (start frame only, fast).
- [ ] `aspect_ratio:"9:16"`; `mode:"std"` (`kling3_0`) or `resolution:"720p"` (Turbo); frames exactly 9:16; output verified with ffprobe and conformed if needed.
- [ ] `sound` string set deliberately; Turbo audio handled in post if silence is needed.
- [ ] Prompt ≤2,500 characters; camera setup first; time markers; one action and one camera move per beat; "real-time speed".
- [ ] Multi-shot approach chosen (continuous / experimental labels / one clip per shot).
- [ ] Every person/product Element tagged at every mention; frames and Element images text-free.
- [ ] Dialogue `Name (tone): "line"`, lowercase English, ≤2 speakers per beat, action before each line.
- [ ] Integration: size, hand/grip, orientation, light direction, reflection and shadow; states restated at later beats.
- [ ] Clean-plate exclusion sentence; quoted strings only for dialogue; scene text only via start frame or exact-words recipe.
- [ ] End frame only with a start frame; `get_cost:true` preflight done.

