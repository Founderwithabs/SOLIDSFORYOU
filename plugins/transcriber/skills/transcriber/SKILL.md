---
name: transcriber
description: Transcribes voice notes, podcasts, calls and videos into text and timestamped captions with OpenAI's Whisper, inside the chat, with nothing to install: just upload the file. Works for English, Hindi, Hinglish and 90+ languages; feeds video editing, YouTube chapters, Shorts and captions.
---

The files this skill uses sit next to this SKILL.md. In Claude Code that
folder is `${CLAUDE_SKILL_DIR}`; anywhere else, use the folder this file was
loaded from. If the files came as text with no folder (for example from a
skill marketplace), save the ones a task needs to a temporary folder, never
the founder's project, and use that. Below, `SKILL_DIR` means that folder.

Follow `SKILL_DIR/transcriber.md`. Transcribe with
`python3 "SKILL_DIR/scripts/transcribe.py" FILE --out-dir <scratch folder>`;
it installs faster-whisper and the verified SOLIDS FOR YOU Whisper model by
itself on first use, and falls back to clear phone instructions if it can't.
