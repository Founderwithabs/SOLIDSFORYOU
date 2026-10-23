# SOLIDS FOR YOU Master (on)

Route every task to the fewest SOLIDS FOR YOU tools it needs. Invoke a tool's
skill only when its row below says so; never load one "just in case".

| Task | Use |
|---|---|
| Question, quick answer | Answer directly, no tools. careful-mode only if money, legal, health or something hard to undo is involved |
| Other work (writing, code, docs, planning) | No tools by default. careful-mode if high-stakes; economy-mode if long and multi-step |
| Make or edit a video | `master` skill: its video workflow |
| Review a video | motion-design-taste; + harsh-buyer-review if for customers; + audio-review if the sound matters |
| Audio | audio-review |
| Social media | social-media; + harsh-buyer-review for posts that sell; + the video workflow to make a reel |
| Feedback on a product, listing, ad, copy or price | harsh-buyer-review; competitor-research first when the feedback needs fresh competitor data |
| Competitors, market or pricing research | competitor-research (its helpers run on Haiku) |
| Other research | economy-mode helpers gather sources; you verify and cite every fact; careful-mode |

Mixed task: use each part's tools. Unsure: pick the row with more checks.

Save credits: no tools for simple tasks; send bulk reading, searching and
reformatting to cheaper helpers (economy-mode); don't re-read files already
in context; keep simple answers short.
Keep quality: careful-mode on anything customers see or that is hard to undo;
maths in code; never invent facts, prices or sources; every review and
sign-off is yours, never a cheaper model's.

Full rules: the `master` skill. A routing line ("Master: video task, using
...") only for tasks that use a tool. Founders can switch Master to
task-specific with `/plugin configure master@solidsforyou`.
