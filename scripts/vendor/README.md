# Vendored files

- `convert_openai_to_hf.py`: from Hugging Face transformers
  (src/transformers/models/whisper/convert_openai_to_hf.py, main branch,
  fetched 2026-10-24), Apache License 2.0 (header kept in the file;
  https://www.apache.org/licenses/LICENSE-2.0). SOLIDS FOR YOU modified it in
  two places, each marked "SOLIDS FOR YOU modification": an import that moved
  in newer transformers releases, and reading Whisper's generation settings
  from a local file built from OpenAI's own whisper package instead of the
  Hugging Face Hub. Used only by `scripts/build_whisper_packages.py`.
