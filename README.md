# Forma Sound Lab — Flask Instrument Music Generator

A responsive web app for generating simple original MIDI patterns using piano, guitar, drums, flute, trumpet, bass, violin, and strings. Select multiple instruments to create a layered arrangement.

## What it does
- Creates a downloadable multi-track MIDI file with any combination of selected instruments, key, scale, tempo, bars, octave, and variation number.
- Uses `pretty_midi` to create MIDI events.
- Has optional GenAI prompt-to-settings support through a Groq-compatible chat completions API.
- Works for MIDI generation without an AI key.
- Includes responsive HTML/CSS/JavaScript UI with a timeless ivory, charcoal, and bronze aesthetic.

## Run locally (Windows)
1. Install Python 3.10+.
2. Extract this project and open its folder in VS Code.
3. In the terminal:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python app.py
   ```
4. Visit http://127.0.0.1:5000

## Enable GenAI
Copy `.env.example` to `.env`, then add your API key to `GROQ_API_KEY`. Never commit `.env` to GitHub. The AI feature translates a text description into music settings; the MIDI notes themselves are generated locally by Python.

## Listen to MIDI
The app downloads `.mid` files. Open them in a MIDI-capable player or a DAW such as MuseScore, GarageBand, Reaper, or another music program. The instrument sound depends on the MIDI player/soundfont. This starter app does not synthesize MP3/WAV audio in the browser.

## About the dataset
This starter version generates simple original patterns and does not download the MAESTRO dataset. MAESTRO is piano-focused; it is not required for generating these instrument patterns. To synthesize WAV audio server-side, install FluidSynth and a General MIDI soundfont, then use `pretty_midi`'s FluidSynth support.
