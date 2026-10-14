## 9. Open questions / unverified behaviour
- Exact output size for a 9:16 start frame at `"768"` and `"1080"` (768-px short edge inferred); whether any portrait
  output falls below a 720-px short edge.
- Text-to-video aspect ratio (only third-party sources say 16:9).
- Identity of `minimax-fast` and whether it supports 768/1080, camera commands or `end_image`.
- Whether Higgsfield rejects, ignores or re-routes `end_image` on 2.3 variants, and `"1080"` with 10 s.
- Whether Higgsfield leaves `prompt_optimizer` on; whether any variant returns audio.
