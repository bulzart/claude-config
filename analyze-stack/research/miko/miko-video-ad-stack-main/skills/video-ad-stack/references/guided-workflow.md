# Guided video ad workflow

Internal workflow for the Video Ad Stack skill. Guide the user naturally; do not ask them to read or invoke this filename.

Default to **guided walkthrough** unless the user explicitly selects end-to-end. Collect inputs progressively at the stage that needs them, not in one long intake. Reuse everything already supplied. Never ask again for answered questions or put credentials into prompts/output files.

1. Follow `miko-brand-research/workflow.md`. Save the sourced brand brief.
2. Follow `miko-reference-video-breakdown/workflow.md`. Complete BOTH ffmpeg/frame inspection and Higgsfield visual/audio analysis on matching coverage. No separate speech-transcription dependency. Missing required evidence blocks advancement.
3. Follow `miko-reference-to-video-plan/workflow.md`. Apply the same concept and measured target duration to the product. Save the new script, beat map, detailed master prompt and product-image attachment map.
4. Follow `miko-higgsfield-video-production/workflow.md`. Generate through official connected Higgsfield tools from text direction plus product images; review, assemble where required, and measure final output within authorized spend.

## Guided walkthrough conversation

### 1. Brand intake and visible research

Ask one bundled question: “Which product are we making an ad for? Send the brand/product website. If you have them, also share product images, Meta Ad Library links, customer reviews, audience notes or existing research.” Website/product identity are the starting inputs; supporting material is optional. Do not make the user find everything the browser can discover.

Follow the research skill using the **visible in-app Codex browser**. Open the supplied sites, inspect the product and search the public Meta Ad Library for the brand when no direct link was provided. Use the browser's actual controls, not search snippets as a substitute for visiting pages. For login, leave the page open and ask the user to sign in, without asking for credentials. Continue other accessible research while awaiting login. Save and show the sourced brand document, including gaps.

### 2. Reference intake and breakdown

After presenting the research, ask: “Send the reference video or videos you want to adapt. Any particular concept or part you want to keep?” Accept files or links such as TikTok/YouTube. Reuse references already supplied. If a link cannot provide inspectable media for BOTH required analysis methods, explain that specific gap and request the video file; do not claim link access succeeded.

Run the full visual/audio breakdown and show it. Then ask: “Would you like me to adapt this concept to your product at the same target length?” Let the user choose a reference if several were supplied without a selection. Do not generate every supplied reference automatically.

### 3. Editable ad preview

On confirmation, create an original product-specific script, timed beat/shot plan, detailed generation prompt, attachment map and final-duration target. Show the full preview, not just a summary. Obtain missing product images before finalizing image roles. Explain clip splitting only when actual model limits require it. Include the proposed generation batch and available estimate/allowance choices.

Say: “Tell me any edits. When you're happy with this version, say ‘generate’.” Revise the preview on feedback and retain a version identifier in run-state. Edits are not generation approval. Do not call paid generation tools during preview.

### 4. Generate the current preview

“Generate” approves the currently shown version and scoped batch, subject to any unresolved budget or mandatory allowance choice. Never apply approval from an older preview after substantive edits. Execute through Higgsfield, review footage, stitch when required and return the playable final output. Fixes beyond authorized spending need a new scoped decision; do not loop paid retries indefinitely.

In **end-to-end** mode, continue without teaching pauses within an explicit existing generation scope/budget. Missing inputs, required allowance choices and additional spend still need resolution. Walkthrough mode always waits for the user's generation instruction even if a budget was supplied earlier.

Save `run-state.md` in the campaign folder with completed stages, artifact paths, pending job IDs and next action. Resume rather than duplicate paid jobs. Keep campaign data and private footage outside the public repository.

## Starter prompt

“Start the video ad stack. Ask me for the brand information first, research it using the visible in-app browser, then ask for my reference video. Show me the breakdown and an editable ad preview. Wait until I say generate before making the video.”

For automatic execution, select end-to-end and provide a budget/allowance preference. This kit requires actual media tools and credits; it is not a standalone rendering application or a first-pass quality guarantee.
