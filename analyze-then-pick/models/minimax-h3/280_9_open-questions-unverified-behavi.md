## 9. Open questions / unverified behaviour
- Exact pixel sizes of 9:16 output at 2K (`minimax_h3`) and 768p (`minimax_h3_max`); 768×1344 is inferred from the
  H3-Base canvas rule.
- Whether Higgsfield's route applies H3-Context-IR or Max's prompt expansion.
- Whether Edit Mode regeneration removes overlays cleanly, and whether 2K regeneration reintroduces them.
- Reference numbering (per modality vs global); how `medias` order is forwarded; last-frame-only support.
- Credit scaling of `batch_size`; billing for reference videos.
- In-frame text accuracy beyond MiniMax's own claims (no independent measurement found).
- Quality gap between H3 Max 768p and H3 2K for identity and product detail.
