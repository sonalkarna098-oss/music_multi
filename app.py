import os
import tempfile
from pathlib import Path

import pretty_midi
from flask import Flask, jsonify, render_template, request, send_file
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

# General MIDI program numbers are zero-based in pretty_midi.
INSTRUMENTS = {
    "piano": {"program": 0, "label": "Acoustic Grand Piano"},
    "guitar": {"program": 24, "label": "Nylon Guitar"},
    "drums": {"program": 0, "label": "Drums / Percussion"},
    "flute": {"program": 73, "label": "Flute"},
    "trumpet": {"program": 56, "label": "Trumpet"},
    "bass": {"program": 32, "label": "Acoustic Bass"},
    "violin": {"program": 40, "label": "Violin"},
    "strings": {"program": 48, "label": "String Ensemble"},
}
NOTE_MAP = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5,
            "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
SCALES = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "pentatonic": [0, 2, 4, 7, 9],
    "blues": [0, 3, 5, 6, 7, 10],
}


def make_midi(settings):
    selected = settings.get("instruments", settings.get("instrument", ["piano"]))
    if isinstance(selected, str):
        selected = [selected]
    if not isinstance(selected, list):
        raise ValueError("Choose one or more instruments.")
    selected = list(dict.fromkeys(selected))
    if not selected or len(selected) > len(INSTRUMENTS):
        raise ValueError("Choose at least one instrument.")
    for key_name in selected:
        if key_name not in INSTRUMENTS:
            raise ValueError("Choose only supported instruments.")

    root = settings.get("key", "C")
    if root not in NOTE_MAP:
        raise ValueError("Choose a valid musical key.")
    scale_name = settings.get("scale", "major")
    if scale_name not in SCALES:
        raise ValueError("Choose a supported scale.")
    try:
        bpm = int(settings.get("bpm", 100))
        bars = int(settings.get("bars", 4))
        octave = int(settings.get("octave", 4))
        seed = int(settings.get("seed", 7))
    except (TypeError, ValueError):
        raise ValueError("Tempo, bars, octave and seed must be numbers.")
    if not 50 <= bpm <= 180:
        raise ValueError("Tempo must be between 50 and 180 BPM.")
    if not 1 <= bars <= 16:
        raise ValueError("Choose between 1 and 16 bars.")
    if not 2 <= octave <= 6:
        raise ValueError("Choose an octave from 2 to 6.")

    import random
    midi = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    root_pitch = 12 * (octave + 1) + NOTE_MAP[root]
    scale_pitches = [root_pitch + step for step in SCALES[scale_name]]
    beat = 60.0 / bpm
    total_beats = bars * 4

    for instrument_key in selected:
        info = INSTRUMENTS[instrument_key]
        track = pretty_midi.Instrument(program=info["program"],
            is_drum=(instrument_key == "drums"), name=info["label"])
        if instrument_key == "drums":
            for bar in range(bars):
                for b in range(4):
                    t = (bar * 4 + b) * beat
                    track.notes.append(pretty_midi.Note(velocity=100, pitch=36, start=t, end=t + beat * .18))
                    if b in (1, 3):
                        track.notes.append(pretty_midi.Note(velocity=92, pitch=38, start=t, end=t + beat * .18))
                    for half in (0, .5):
                        ht = t + half * beat
                        track.notes.append(pretty_midi.Note(velocity=58 if half == 0 else 45,
                            pitch=42, start=ht, end=ht + beat * .12))
        else:
            local_rng = random.Random(seed + list(INSTRUMENTS).index(instrument_key) * 137)
            for i in range(total_beats):
                start = i * beat
                if i % 8 in (3, 7) and local_rng.random() < .45:
                    continue
                pitch = local_rng.choice(scale_pitches)
                if local_rng.random() < .15:
                    pitch += 12
                if instrument_key == "bass":
                    pitch -= 12
                if instrument_key in ("violin", "flute", "trumpet"):
                    pitch += 12
                duration = beat * (.8 if instrument_key in ("flute", "trumpet", "violin") else .65)
                velocity = local_rng.randint(65, 100)
                track.notes.append(pretty_midi.Note(velocity=velocity,
                    pitch=max(24, min(108, pitch)), start=start, end=start + duration))
                if instrument_key in ("piano", "guitar", "strings") and i % 4 == 0:
                    for cp in [scale_pitches[0], scale_pitches[2], scale_pitches[4]]:
                        track.notes.append(pretty_midi.Note(velocity=max(42, velocity - 18),
                            pitch=min(108, cp), start=start, end=start + beat * 1.7))
        midi.instruments.append(track)

    return midi, {
        "instruments": [INSTRUMENTS[k]["label"] for k in selected],
        "instrument_count": len(selected), "bpm": bpm, "bars": bars,
        "key": root, "scale": scale_name,
        "duration_seconds": round(total_beats * beat, 2),
        "note_count": sum(len(inst.notes) for inst in midi.instruments),
    }

@app.get("/")
def home():
    return render_template("index.html", instruments=INSTRUMENTS)

@app.post("/api/generate")
def generate():
    data = request.get_json(silent=True) or {}
    try:
        midi, info = make_midi(data)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mid") as temp:
            midi.write(temp.name)
            path = temp.name
        # The UI downloads the generated MIDI; no audio renderer is required.
        response = jsonify({"ok": True, "info": info, "download_url": f"/download/{Path(path).name}"})
        response.headers["X-Generated-File"] = Path(path).name
        return response
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

@app.get("/download/<filename>")
def download(filename):
    # Only serve MIDI files generated into the OS temp directory by this app.
    if not filename.endswith(".mid") or "/" in filename or "\\" in filename:
        return "Invalid file", 400
    path = os.path.join(tempfile.gettempdir(), filename)
    if not os.path.isfile(path):
        return "File not found. Generate a new track first.", 404
    return send_file(path, as_attachment=True, download_name="forma-generated-music.mid",
                     mimetype="audio/midi")

@app.post("/api/ai-prompt")
def ai_prompt():
    # Optional GenAI mode: ask an OpenAI-compatible endpoint to suggest musical settings.
    import requests
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return jsonify({"ok": False, "error": "AI prompt suggestions need GROQ_API_KEY in your .env file. The music generator works without it."}), 503
    data = request.get_json(silent=True) or {}
    prompt = str(data.get("prompt", "")).strip()
    if not prompt or len(prompt) > 600:
        return jsonify({"ok": False, "error": "Enter a music idea under 600 characters."}), 400
    try:
        endpoint = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        r = requests.post(endpoint, headers={"Authorization": f"Bearer {api_key}"},
            json={"model": model, "temperature": 0.2, "max_tokens": 180,
                  "messages":[
                      {"role":"system","content":"You are a music arrangement assistant. Map the user's idea to JSON only with keys instrument (one of piano,guitar,drums,flute,trumpet,bass,violin,strings), key (C,C#,D,D#,E,F,F#,G,G#,A,A#,B), scale (major,minor,pentatonic,blues), bpm (50-180), bars (1-16), octave (2-6), seed (integer). Pick a sensible match. No markdown."},
                      {"role":"user","content":prompt}]}, timeout=20)
        r.raise_for_status()
        import json, re
        content = r.json()["choices"][0]["message"]["content"].strip()
        content = re.sub(r"^```(?:json)?|```$", "", content, flags=re.M).strip()
        settings = json.loads(content)
        # Validate settings with the same generator before returning.
        _, info = make_midi(settings)
        return jsonify({"ok": True, "settings": settings, "summary": info})
    except Exception:
        return jsonify({"ok": False, "error": "Could not create a suggestion. Check your API settings or try a simpler description."}), 502

if __name__ == "__main__":
    app.run(debug=True)
