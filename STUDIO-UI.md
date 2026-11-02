# Studio audiobooks in the web app (manual / browser use)

The fallback when the Studio API answers `403 invalid_subscription` ("requires your account to be explicitly
whitelisted"): a Pro plan includes Studio on the website, but not its API. Everything below was verified in
the ElevenLabs web app (Nov 2026) with a browser tool. UI labels may move; the rules are what matters.

## Ground rules

- **The person signs in.** Never type their password or use their Google/Apple sign-in. Ask them to sign in
  in the browser pane, then continue.
- **Uploading a file.** The built-in browser pane cannot pick files. Either ask the person to drag the file
  into the upload box, or use a browser tool that can upload (Claude in Chrome's `file_upload`).
- **Credits.** Importing, casting, editing and the Export panel's estimate are free. Audio is generated, and
  credits spent, only by **Generate** (paragraph/chapter) or **Export** with ungenerated paragraphs.
  The wizard's "Queueing… / NN% generated" after *Create audiobook* is the text and casting analysis,
  not audio (verified: balance unchanged, "No generation found"). Ask before Generate or Export.
- **Playing spends credits too**: ▶ in the editor's player generates every ungenerated paragraph it reaches
  (the top bar shows "Generating…"). Never press play to "check" a project.
- Check the balance before and after with `quota.py` (character count) or the "credits remaining" in the
  project's top bar.

## Prepare the document

Studio imports **EPUB, PDF or DOCX**. Its importer **starts a new chapter at every heading level** (H1, H2
and H3 alike), and a heading's text is spoken. So:

- One heading per chapter (H1), worded as it should be heard. Rename the chapter afterwards in the Chapters
  panel if the display name should differ.
- Section titles inside a chapter are ordinary paragraphs, not headings.
- Write the text as it should be spoken (numbers, abbreviations, case names already expanded) and set text
  normalization in Project settings to suit. One paragraph per block; paragraph breaks become Studio blocks.
- Keep a list of which paragraphs belong to which voice (first and last words of every run), plus the
  character count per voice: it is the check at the end.

## Create the project (Audiobooks → Create a new project → Create an Audiobook)

1. **Upload**: the file, the narration style and the model (default Eleven v4).
   - *Single cast*: one voice for everything.
   - *Multi cast*: a Narrator plus AI-detected characters. Quoted sentences (“…”) come out as an
     "Unnamed speaker"; everything else is Narrator. Use Multi cast for two-voice books: it creates the
     second character for you and already assigns quoted examples to it.
2. **Formatting**: cover image, the chapter list (check its count against your chapters: a surplus
   means headings inside chapters), language, scene break length (silence at scene breaks, default 1.0s).
3. **Characters**: name, description, preview line and voice per character (tabs Recommended / Explore /
   My Voices). Click the character, open **My Voices**, search the voice by name and click its name (not
   ▶). Check the list afterwards: each row reads "(Voiced by …)". Add a character with **+ Add character**
   for every voice the book needs (e.g. a commentary voice), not only the ones the casting detected.
   Setting every voice here is cheapest: changing a voice later clears audio already generated.
4. **Pronunciations**: suggested terms with Alias or phoneme rules per character. Empty rules are skipped.
5. **Create audiobook**: the project opens in the editor.

## In the editor

Left rail: **Edit**, **Chapters**, **Characters**, **Pronunciations**, **SFX**, **Music**, **Files**.

- **Characters panel**: **clicking a character's row assigns the current text selection to that
  character** (the ✓ moves to it). Undo (↶ top left) if that happened by accident. To edit a character
  instead, hover its row and click the **settings icon** (sliders) that appears. There you set the name,
  description, voice volume, stability and "clone strength" (similarity). **+** at the top adds a character.
- **Changing a character's voice**: settings icon → **Voice** → *Voice casting* → **My Voices** → search
  by name → click the voice's name. Do not press ▶ (a preview) and do not use the "Voice" prompt box at
  the bottom (voice design, 350 credits). Studio then shows **Reassign character voice**, listing the chapters
  and paragraph counts on that character, with **Assign and clear impacted audio**: generated audio of those
  paragraphs is discarded and must be paid for again. Only confirm when none of it is generated (Export
  estimate below), or when the person agrees. Cancel otherwise.
- To move paragraphs to another voice without touching the character, select them and pick the other
  character in the Edit panel (next item).
- **Assigning paragraphs to a voice**: click at the start of the run's first paragraph, shift-click in
  its last paragraph. The Edit panel then reads "Edit Speech (N)". Choose the character from its
  **Character** dropdown, which applies it to all N paragraphs. Each paragraph shows the character's
  initial in its left badge (N = Narrator, U = Unnamed speaker, …). Clicking a badge opens that
  character's settings instead.
- **Edit panel** for the selected paragraph(s): volume, fade in/out, type (Heading 1 / Text), character,
  generation history, AI tools (Enhance text, voice isolator, voice changer, record your own) and a
  per-paragraph model override.
- **Project settings** (☰ top left → Project settings):
  - *General*: model, default character, language, ISBN.
  - *Export*: title, author, cover, description, genre. These are written as metadata into the downloads.
  - *Advanced*: text normalization (auto / on / off) and **volume normalization** (audiobook standard:
    −3 dB ceiling, −18 to −23 dB RMS).
- Version history is in the ☰ menu.

## Check before spending

**Export** (top right) → *Export* tab, before clicking the button. It shows the scope (full project or
chapter), media type, file structure (**Single file** or **Chapters ZIP**), format (**MP3** or **WAV**) and
"It will cost N credits", **broken down by voice**. Compare that breakdown with your per-voice character
counts. A mismatch means paragraphs are still on the wrong character. Close the panel without exporting
until it matches. The estimate covers only *remaining* (ungenerated) paragraphs. If it drops below the
document's total, some audio has been generated, and voice changes would clear it.

## Generate and download

Ask first: this spends the credits shown. Either **Generate** per chapter/paragraph and review, or Export,
which generates what is missing. The *History* tab of the Export panel lists earlier exports for download.
The *Publish* tab offers ElevenReader, Spotify, InAudio, ElevenLabs Video and Audio Native.
