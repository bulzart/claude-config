## 6. Elements — reusable project assets

`show_reference_elements` stores a character, prop or environment once per workspace; prompts cite it
as `<<<element_id>>>` and the backend injects the image [HF-TOOL].

- **Create.** `show_reference_elements {action:"create", medias:[{id:<media_id>, url:<upload url>, type:"media_input"}], category:"character"|"prop"|"environment"|"auto", name:"<≤32 chars>", description:"<optional>"}`.
  It returns synchronously. A completed image job can serve as the source (`type:"image_job"`).
- **Video models that accept Elements**: Cinema Studio Video 2 / 3.0, Seedance 2.0, Kling 3.0 (per the
  tool description). Several placeholders per prompt are allowed:
  `"<<<A>>> hands <<<B>>> to the person on the left"`.
- **When to use.** Analyze Mode collects project-level characters and products once. Create Elements
  for them when the selected model is on the list above; this matters most for Kling 3.0 and Cinema
  Studio, whose catalog entries have no `image_references` role. Store element ids in
  `state.json → assets`.
- **Ambiguity guard.** The tool asks the agent to choose between a Soul (5–20 photos, image models
  only) and an Element (instant, one image, multi-subject). For video generation, Elements are the
  relevant path.

