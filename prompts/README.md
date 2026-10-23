# Paste-in prompts

Each SOLIDS FOR YOU tool also works as a plain prompt in any Claude chat. Open
the prompt, copy all of it, and paste it as your first message, or into a
Claude Project's instructions.

| Tool | Prompt | Fill in first |
|---|---|---|
| Audio Review | [initiation_prompt.md](../plugins/audio-review/skills/audio-review/initiation_prompt.md) | Nothing. Upload your audio after Claude replies |
| Motion Design Taste | [motion-design-taste.md](../plugins/motion-design-taste/skills/motion-design-taste/motion-design-taste.md) | Nothing. Claude asks for the video and references |
| Harsh Buyer Review | [harsh-buyer-reviewer.md](../plugins/harsh-buyer-review/skills/harsh-buyer-review/harsh-buyer-reviewer.md) | Sections 1 to 3: your product, price, market and buyer |
| Careful Mode | [careful-mode.md](../plugins/careful-mode/skills/careful-mode/careful-mode.md) | Nothing |

Economy Mode has no paste-in version, because it needs Claude Code's
subagents.

**Shortcut for a Claude that can browse the web:** instead of pasting, send it
the prompt's raw link and ask it to follow it. For example:

> Read https://raw.githubusercontent.com/Founderwithabs/SOLIDSFORYOU/main/plugins/harsh-buyer-review/skills/harsh-buyer-review/harsh-buyer-reviewer.md and follow it for this conversation.
