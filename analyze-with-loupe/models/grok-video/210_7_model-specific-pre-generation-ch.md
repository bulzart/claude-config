## 7. Model-specific pre-generation checklist

- [ ] Start frame conformed to exactly 9:16 (never stretched); classic sends `"9:16"`, 1.5 relies on the frame.
- [ ] 1.5 at `resolution: "720p"`; reference mode only after a probe returns 720×1280.
- [ ] No `start_image` together with references on 1.5 [HF].
- [ ] Motion-first prompt: direction, what stays still, one camera move, "real-time pace", shortest fitting duration.
- [ ] Tags from `<IMAGE_0>`, each with a description; voice clip approved and ≤15 s.
- [ ] Clean plate (blank surfaces plus exclusion line); Analyze-Mode text planned for post.
- [ ] Integration phrases (scale, contact, grip, light, shadow, persistent states).
- [ ] `get_cost` done; output probed (dimensions; classic may be 480p) and QC'd.

