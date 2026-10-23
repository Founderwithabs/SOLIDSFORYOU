---
name: audio-review
description: Listen to an audio file and judge its quality the way a senior audio designer would (loudness, dynamics, tonal balance, stereo, noise, artifacts, delivery specs), then give a scored review with concrete fixes. Use when the user shares an audio or video file (wav, mp3, m4a, flac, ogg, aif, mp4, mov) and asks how it sounds, whether it is good or ready, to check the mix or master, to judge quality, or says "/audio-review".
---

This lets the skill work in sessions opened inside this repository. The real
skill ships as a plugin: read
`plugins/audio-review/skills/audio-review/SKILL.md` and follow it, with
`SKILL_DIR` = `plugins/audio-review/skills/audio-review` (relative to the
repository root).
