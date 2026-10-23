---
name: audio-review
description: Listen to an audio file and judge its quality the way a senior audio designer would (loudness, dynamics, tonal balance, stereo, noise, artifacts, delivery specs), then give a scored review with concrete fixes. Use when the user shares an audio or video file (wav, mp3, m4a, flac, ogg, aif, mp4, mov) and asks how it sounds, whether it is good or ready, to check the mix or master, to judge quality, or asks for an audio review.
---

This lets the tool work in sessions opened inside this repository. The real
skill ships as a plugin. Read `plugins/audio-review/skills/audio-review/SKILL.md` and follow it.
Wherever that file refers to `SKILL_DIR` or to the skill's own folder, use
`plugins/audio-review/skills/audio-review` (relative to the repository root).
