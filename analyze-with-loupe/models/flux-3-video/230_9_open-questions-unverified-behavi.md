## 9. Open questions / unverified behaviour

- **Role mapping (highest priority).** What `image_references` and `video_references` do on Higgsfield (identity reference vs keyframe; continuation vs recast), and how many images are forwarded.
- Whether `start_image`/`end_image` can be combined with `image_references` (BFL returns 422 for keyframes plus references).
- Whether more than two keyframes (storyboard) can be sent, and how they are timed.
- That Higgsfield `720p` equals BFL `hd` (704×1280 at 9:16). Confirm by ffprobe.
- Behaviour when `duration` exceeds 15 with a video input (snap, clamp or error).
- Credit effect of `generate_audio`; drift during early access (`version: latest`).
