# SOLIDS FOR YOU Transcriber

Turns a voice note, podcast, call recording or video into text, with
timestamps, inside the chat's own sandbox, using OpenAI's Whisper. The
founder only uploads the file; nothing to install or set up.

## 1. Rules

- **The audio stays in the sandbox.** Never send it to another service
  unless the founder asks for that service by name.
- **Recordings of other people need their consent.** If a file sounds like
  a call or meeting, check the founder has it before sharing the transcript
  further.
- **Say what you're unsure of.** Whisper mishears names, brands, numbers and
  mixed languages. Mark doubtful words instead of guessing, and never
  "correct" the transcript into something the speaker didn't say.
- **Quotes are exact.** When a transcript is used for posts, listings or
  reviews, quote it word for word or say it's paraphrased.

## 2. Transcribe

Run the bundled script (next to this skill's SKILL.md) on the uploaded file:

```
python3 "SKILL_DIR/scripts/transcribe.py" "<file>" --out-dir <scratch folder>
```

Useful options:
- `--language hi` (or `en`, `ta`, ...) when you know the language; default
  is automatic detection.
- `--prompt "names and words to expect"`: brand and product names, people's
  names, jargon. For Hinglish in Roman script, a short Roman Hinglish example
  in the prompt usually keeps the output in Roman letters.
- `--translate`: English translation of the speech.
- `--size small`: slower but more accurate (default `base`).

The first run installs the engine and model by itself (a minute or two);
later runs reuse them. It accepts audio and video files (m4a, mp3, wav,
ogg, opus, mp4, mov and more).

## 3. Reply in chat

1. The full transcript (or, for long recordings, a summary first and the
   full text after), with doubtful words marked.
2. The language detected and the duration.
3. The files written: `.txt`, `.srt` and `.vtt` captions, and `.json` with
   word timings. Offer them as downloads where the chat allows.
4. What the founder can do next with it (section 4).

## 4. What the transcript feeds

- **Rough-cut a video:** the `master` skill's `transcript_edit.py` (dead
  air, filler, retakes; `--apply` cuts the video).
- **YouTube:** chapters, Shorts selection and retention analysis in the
  `social-media` skill (`youtube.md`).
- **Captions:** burn the `.srt` into a video with the `master` skill's video
  workflow, or upload it to the platform.
- **Content:** posts, threads, quotes and blog drafts from what the founder
  said, in their own voice (`social-media`).

## 5. When it can't run

If the sandbox can't install packages or load the model, the script says
so and lists phone options: Voice Memos transcripts on iPhone, the Recorder
app on Android, YouTube's automatic captions (upload unlisted), and
Instagram or TikTok auto-captions. Ask the founder to paste the text or
`.srt`, then continue from section 3.

Without any code tool at all, say you can't listen to audio in this chat and
offer the same options.
