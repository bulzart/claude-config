---
name: video-ad-stack
description: Guide the user from brand research and reference video analysis through an editable ad plan to Higgsfield video generation. Use when the user says start the video ad stack, run the video ad stack, or asks for this guided product-ad workflow.
---

# Video Ad Stack

Start the guided workflow immediately when invoked. The user should never need to name internal files, choose individual skills or supply every input up front. Within an already active stack, “start” means begin the next unfinished intake; do not interpret a generic start message outside this context as authorization to run it.

Read [the guided workflow](references/guided-workflow.md), then load each stage's supporting instructions only when that stage is reached. Resolve stage paths relative to that guide. The four stages are internal parts of this single skill, not separate skills the user must install.

If starting with no product information, ask: “What product are we making an ad for? Send the brand or product website. You can also share product images, ad-library links or research you already have.” If information is already supplied, use it and ask only for the missing inputs needed now.

Guide the user through visible in-app browser research, reference intake, ffmpeg plus Higgsfield visual/audio analysis, adaptation and an editable preview. Wait for the user's “generate” instruction before paid generation in guided mode. Preserve all spending and version-approval rules in the guide. End-to-end mode is available only when explicitly requested within authorized scope.

Keep conversation natural: explain the current stage and show its output. Do not ask the user to run commands, read workflow files or manage internal stage routing when your tools can do it. Missing tools or login access must be disclosed accurately. A skill cannot register a universal `/start` command in the host application; support natural-language invocation without promising such an alias.
