## 4. Prompt construction
### 4.0 Examples and patterns
1. "Replace [the object in the source video] with [the object in the reference image]. Keep the rest
   of the shot the same." — The Rundown, Genjutsu Object Swap guide [SECONDARY].
2. "Replace one clearly defined object with the object shown in @Image 2, while leaving the performer,
   background, lighting direction, and camera path stable. The swap should track perspective and
   shadows across the shot." — practitioner template reported alongside that guide [SECONDARY].
3. Higgsfield's own edit contract (`first-party/ad-multiplier-prompt-writer.md`, Seedance-2.5-based,
   first-party): "Replace only [target] in @Video1 with [replacement] from [@ImageN]" and "Remove only
   [target] from @Video1 and reconstruct the revealed area consistently with its immediate
   surroundings" [HF].

Patterns:
- one imperative operation per sentence;
- the target identified uniquely;
- the replacement bound to its image tag;
- the explicit keep-list (performer, background, light, camera path);
- a tracking clause for perspective and shadows;
- no scene re-description.

### 4.4 Object Swap template
```text
Replace only <unique target description> in @Video1 with <replacement name> from @Image1<, @Image2 (other views of the same item)>. Keep its exact shape, proportions, colours and markings from the reference images at <real-world size relative to hand/body>; do not take on the original object's shape. It follows the original's exact position, path, orientation, grip and occlusion in every frame, matches the scene's light direction and colour, and casts consistent shadows and reflections. The original <target> must not appear in any frame. Remove <source captions / usernames / watermark>, reconstructing the background behind them. Keep the performer, motion, camera path, framing, lighting and timing of @Video1 unchanged.
```
Example: "Replace only the white ceramic mug held in the man's right hand in @Video1 with the matte
black insulated tumbler from @Image1 and @Image2 (front and side of the same tumbler). Keep its exact
tall cylindrical shape, lid and proportions from the references, about the height of his hand; do not
take on the mug's shape or handle. It follows the mug's exact position, path, tilt and grip in every
frame, matches the warm window light from the left and casts a consistent soft shadow. The mug must
not appear in any frame. Keep the man, his motion, the camera path and the timing of @Video1
unchanged."

### 4.4 Motion Transfer template
```text
Transfer the full-body motion, gesture timing and camera movement of @Video1 to <subject> from @Image1. <Subject> keeps the face, hair, body proportions and complete outfit shown in @Image1<; the scene is the <location> from @Image2 | described scene>. Do not use the person, clothing, props or background of @Video1. Real-time speed; the same cuts and camera path as @Video1.
```

