# Zoom Real-Time Speech-to-Speech Translator

Live bidirectional translation for Zoom calls using Google Gemini S2ST.

## Quick Start

### Prerequisites
```bash
brew install blackhole-2ch    # Virtual audio driver (reboot after install)
pip install google-genai pyaudio numpy python-dotenv
gcloud auth application-default login
```

### Setup .env
```
GOOGLE_CLOUD_PROJECT=your-project-id
GEMINI_MODEL=gemini-live-2.5-flash-native-audio
```

### Zoom Audio Settings
1. **Zoom > Settings > Audio > Microphone:** BlackHole 2ch
2. **Zoom > Settings > Audio > Speaker:** BlackHole 2ch

### Run (CLI)
```bash
# Terminal 1: Your voice → Japanese → Zoom
python3 translate.py upstream --target ja

# Terminal 2: Zoom audio → English → Your speakers
python3 translate.py downstream --target en --speaker-index 5
```

### Run (Electron UI)
```bash
cd electron && npm install && npm run dev
```
Select your mic and speaker, click Start.

## How It Works
```
YOU SPEAK → Mic → Gemini S2ST → BlackHole → Zoom (partner hears Japanese)
PARTNER SPEAKS → Zoom → BlackHole → Gemini S2ST → Speakers (you hear English)
```

## Supported Languages
en, ja, es, fr, de, cmn, ko, hi, ar, pt, it, ru, nl, sv, pl, tr, vi, th + 80 more

## Useful Commands
```bash
python3 translate.py --list-devices    # See audio device indices
```
