## 1. The dependency chain

```
source analysis ──► content strategy ──► style + subject (selected direction) ──► concept
      │                                                                               │
      │                          client assets needed ◄──────────────────────────────┘
      │                                  │
      │        asset geometry, identity, materials constrain ──► placement, interaction, staging
      │                                  │
      │        environment constrains ──► perspective, lighting, reflections, shadows, motion
      │
      └──► reference mechanics ──► pacing, hook, camera behaviour, engagement structure
                                                   │
official model docs + official examples ──► how the intentions are expressed (prompt structure, syntax)
Higgsfield capabilities ──► how references, parameters and operations are actually passed
final QC ──► every decision checked against every other decision
```

When a decision changes upstream (e.g. a different asset), re-run every downstream step that depends
on it. Do not patch the prompt alone.

