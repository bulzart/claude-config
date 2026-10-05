# Miko Video Ad Stack

[**Join 1000+ Marketers Inside Content System AI →**](https://whop.com/theaicontentsystem/products/ai-content-accelerator-ed/)

One skill that walks you through making a video ad: brand research → reference breakdown → editable ad plan → Higgsfield generation.

Once the skill is loaded, just say:

> **Start the video ad stack.**

It asks for your brand information, researches in the visible in-app browser, asks for reference videos, shows the breakdown, helps adapt the concept to your product and previews the script and generation plan. Make edits, then say **generate** when you're ready.

## Setup

Download with **Code → Download ZIP** and extract, or clone with Git. Open this folder as a local project in an agent with local tools. Connect official Higgsfield separately. Verify visible in-app browser access, ffmpeg/ffprobe, frame inspection and Higgsfield visual/audio analysis. No separate speech-transcription dependency is required. Generation credits are separate. Never paste keys into chat or commit credentials.

**Guided walkthrough is the default.** You do not need to name internal files or run four separate skills. It requests information when needed, remembers your answers and waits for generation approval. Choose **end-to-end** explicitly to continue within authorized scope without teaching pauses. Keep campaign outputs outside this public repository.

For native discovery, copy the single `skills/video-ad-stack` folder, including all its contents, into your local project's `.agents/skills/`. Preserve existing skills. Open a fresh task and verify **video-ad-stack** is available. Then say **Start the video ad stack**. Cloning alone does not install skills or connect tools. See the official [skill guide](https://learn.chatgpt.com/docs/build-skills) and [local projects guide](https://learn.chatgpt.com/docs/projects). Local and cloud projects have different file-access paths.

Alternatively, open the downloaded repository in your local agent and say: “Read the Video Ad Stack skill and start it.” The entry is [Video Ad Stack](skills/video-ad-stack/SKILL.md). You do not need to say “follow RUN-STACK.md.”

**Preview release:** structure validated; real end-to-end campaign pilot still pending. The analyzer incorporates Miko's Video Breakdown SOP. Both ffmpeg/frame inspection and Higgsfield analysis are required in the stack, plus speech verification when applicable. The planner produces detailed text direction with product-image references at the source target length. This is a skill kit requiring tools and credits, not hosted rendering software.

Before calling this production-tested, complete a real brand/reference pilot and verify target-app setup. Public GitHub files are accessible without joining a community.

The skill contains four internal stages. Brand research and video analysis converge in adaptation. Analysis uses ffmpeg/frame inspection plus Higgsfield visual/audio analysis, without a separate speech-transcription dependency. Generation uses detailed text direction and your product images at the reference's target duration where supported.

## More from Miko

[AI Content System](https://whop.com/theaicontentsystem/products/ai-content-accelerator-ed/) — further workflows and resources. Provider credits and private hosted systems are not included.
