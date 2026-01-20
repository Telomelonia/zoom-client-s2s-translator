# S2ST Options Research

**Date:** 2025-01-21
**Status:** BLOCKED

---

## What We Need
- True speech-to-speech translation (not text intermediary)
- Preserves voice characteristics
- Low latency (<500ms)
- 70+ languages

---

## Options Evaluated

### 1. Google Gemini S2ST ❌ BLOCKED
- Model: `gemini-2.5-flash-s2st-exp-11-2025`
- True S2ST, FREE during preview
- **Blocker:** Requires GCP billing enabled
- Test script: `test_s2st_access.py`

### 2. Gemini Native Audio ❌ REJECTED
- Just a voice assistant, not true S2ST

### 3. Meta SeamlessM4T ⚠️ VIABLE
- True S2ST, open source, FREE
- **Blocker:** Needs cloud GPU (A100/H100)
- Too slow on M3 Pro Mac

### 4. NVIDIA PersonaPlex ❌ WRONG USE CASE
- Not translation, it's conversational AI

---

## Path Forward

| Option | Cost |
|--------|------|
| Enable GCP billing | Free trial ($300) |
| Rent cloud GPU | ~$0.50-2/hr |

**Decision needed.**
