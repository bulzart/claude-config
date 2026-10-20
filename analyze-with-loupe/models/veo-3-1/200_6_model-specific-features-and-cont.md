## 6. Model-specific features and controls

- **Variants (`veo3_1`):** `veo-3-1-fast` (default) for iteration, `veo-3-1-preview` for finals [HF]. Google positions Fast for ads, rapid A/B testing and social content [OFFICIAL].
- **Quality tiers (`veo3_1`):** always `basic` in the fixed format (§2.6).
- **Lite as the draft tier:** less than half the cost of Fast [OFFICIAL]. The only id here with an end frame and an audio switch [HF]. Lock the prompt on Lite, then render the final on `veo3_1` from the same start frame [INFERRED].
- **Timestamp prompting and native audio** [OFFICIAL].
- **Prompt enhancement via Gemini** [OFFICIAL]. Keep the result under 1,024 tokens.
- **SynthID** invisible watermark [OFFICIAL].

