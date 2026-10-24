# Paste-in prompts

Each SOLIDS FOR YOU tool also works as a plain prompt in any Claude chat. Open
the prompt, copy all of it, and paste it as your first message, or into a
Claude Project's instructions.

| Tool | Prompt | Fill in first |
|---|---|---|
| Audio Review | [initiation_prompt.md](../plugins/audio-review/skills/audio-review/initiation_prompt.md) | Nothing. Upload your audio after Claude replies |
| Motion Design Taste | [motion-design-taste.md](../plugins/motion-design-taste/skills/motion-design-taste/motion-design-taste.md) | Nothing. Claude asks for the video and references |
| Harsh Buyer Review | [harsh-buyer-reviewer.md](../plugins/harsh-buyer-review/skills/harsh-buyer-review/harsh-buyer-reviewer.md) | Sections 1 to 3: your product, price, market and buyer |
| Social Media | [social-media.md](../plugins/social-media/skills/social-media/social-media.md) | Nothing. Claude asks about your brand, audience and goal the first time |
| AI Visuals | [ai-visuals.md](../plugins/ai-visuals/skills/ai-visuals/ai-visuals.md), plus the placement's section of [purposes.md](../plugins/ai-visuals/skills/ai-visuals/purposes.md) and the tool's section of [generators.md](../plugins/ai-visuals/skills/ai-visuals/generators.md) | Nothing. Share the image or video, the prompt you used and where it will go |
| Ecom | [ecom.md](../plugins/ecom/skills/ecom/ecom.md), plus the module you need from [modules/](../plugins/ecom/skills/ecom/modules/) and the marketplace's section of [marketplaces.md](../plugins/ecom/skills/ecom/marketplaces.md) | Nothing. Claude asks for your products, costs and channels the first time |
| Competitor Research | [competitor-research.md](../plugins/competitor-research/skills/competitor-research/competitor-research.md) | Nothing. Claude asks for your product and the question. Pick Haiku as the model to save credits |
| Careful Mode | [careful-mode.md](../plugins/careful-mode/skills/careful-mode/careful-mode.md) | Nothing |
| Master Skill | [master-full.md](../dist/master-full.md) (the Master Skill with every tool and the video workflow, in one file) | Nothing. Claude picks the tools each task needs |

Economy Mode has no paste-in version, because it needs Claude Code's
subagents.

**Shortcut for a Claude that can browse the web:** instead of pasting, send it
the prompt's raw link and ask it to follow it. For example:

> Read https://raw.githubusercontent.com/Founderwithabs/SOLIDSFORYOU/main/plugins/harsh-buyer-review/skills/harsh-buyer-review/harsh-buyer-reviewer.md and follow it for this conversation.
