# Zoom S2S Translator - Development Guide

## Quick Start

### Prerequisites

- **Node.js** >= 20.0.0 ([Download](https://nodejs.org/))
- **Python** >= 3.10 ([Download](https://www.python.org/))
- **Homebrew** (macOS only, for BlackHole installation)
- **Google Cloud Account** with Vertex AI API enabled

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd zoom-client-s2s-translator
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and fill in your Google Cloud credentials
   ```

3. **Install BlackHole (macOS only)**
   ```bash
   chmod +x scripts/install-blackhole.sh
   ./scripts/install-blackhole.sh
   ```

4. **Install dependencies and start development**
   ```bash
   chmod +x scripts/dev.sh
   ./scripts/dev.sh
   ```

   This script will:
   - Check Node.js and Python versions
   - Install Electron dependencies
   - Create Python virtual environment
   - Install Python dependencies
   - Start both Electron and Python backend

### Manual Setup (if preferred)

**Electron:**
```bash
cd electron
npm install
npm run dev
```

**Python:**
```bash
cd python
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 src/main.py
```

## Project Structure

```
zoom-client-s2s-translator/
├── electron/              # Electron frontend
│   ├── src/
│   │   ├── main/         # Main process (Node.js)
│   │   ├── renderer/     # UI (HTML/CSS/TS)
│   │   ├── preload/      # IPC bridge
│   │   └── shared/       # Shared types
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── electron-builder.yml
├── python/               # Python backend
│   ├── src/
│   │   ├── audio/       # Audio capture/playback
│   │   ├── gemini/      # Vertex AI integration
│   │   └── routing/     # Audio routing
│   ├── requirements.txt
│   └── pyproject.toml
├── scripts/             # Development scripts
│   ├── dev.sh          # Start dev environment
│   └── install-blackhole.sh
├── docs/               # Documentation
│   ├── SPEC.md         # Full specification
│   ├── ARCHITECTURE.md # Technical design
│   └── PROJECT_STATUS.md
├── .env.example        # Environment template
└── CLAUDE.md          # Project intelligence
```

## Available Scripts

### Electron (in `/electron` directory)

- `npm run dev` - Start Vite dev server with hot reload
- `npm run build` - Build TypeScript and bundle
- `npm run start` - Start Electron app
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Fix ESLint errors
- `npm run format` - Format code with Prettier
- `npm run typecheck` - Run TypeScript type checking
- `npm run build:electron` - Build distributable packages

### Python (in `/python` directory, with venv activated)

- `python3 src/main.py` - Run backend
- `pytest` - Run tests
- `pytest --cov` - Run tests with coverage
- `ruff check .` - Run linter
- `ruff check . --fix` - Fix linting errors
- `black .` - Format code
- `mypy src/` - Run type checker

## Development Workflow

### 1. Feature Development

1. Create a feature branch
2. Write code following clean code principles
3. Ensure TypeScript/Python type checking passes
4. Run linters (ESLint/Ruff)
5. Format code (Prettier/Black)
6. Write tests
7. Update documentation

### 2. Code Quality Standards

**TypeScript:**
- Strict mode enabled
- Explicit function return types
- No `any` types
- No unused variables
- Consistent formatting via Prettier

**Python:**
- Type hints required
- Ruff for linting
- Black for formatting
- mypy for type checking
- 88 character line length

### 3. Testing

**Electron:**
- Place tests in `electron/tests/`
- Run with test framework (TODO: configure)

**Python:**
- Place tests in `python/tests/`
- Run with `pytest`
- Aim for 80%+ coverage

## Environment Variables

See `.env.example` for all available options. Required:

- `GOOGLE_APPLICATION_CREDENTIALS` - Path to service account JSON
- `GOOGLE_CLOUD_PROJECT` - Your GCP project ID
- `VERTEX_AI_LOCATION` - GCP region (e.g., `us-central1`)

## Troubleshooting

### "Cannot find module" errors in Electron

```bash
cd electron
rm -rf node_modules package-lock.json
npm install
```

### Python import errors

```bash
cd python
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### BlackHole not appearing in audio devices (macOS)

1. Restart your computer
2. Check System Settings > Sound
3. Reinstall: `brew reinstall --cask blackhole-2ch`

### TypeScript errors in Electron

```bash
cd electron
npm run typecheck
```

Fix any type errors before running the app.

### Python linting errors

```bash
cd python
source venv/bin/activate
ruff check . --fix
black .
```

## Next Steps

After completing Phase 1 setup, proceed to Phase 2:

1. **Audio Capture** - Implement microphone and system audio capture
2. **Gemini Integration** - Connect to Vertex AI S2ST API
3. **Audio Routing** - Route translated audio through virtual devices

See `docs/SPEC.md` for detailed phase breakdowns.

## Getting Help

- Check `docs/SPEC.md` for detailed specifications
- Check `docs/ARCHITECTURE.md` for system design
- Check `docs/PROJECT_STATUS.md` for current progress
- Review `CLAUDE.md` for project intelligence and standards

## Contributing

1. Follow the clean code principles in `CLAUDE.md`
2. Ensure all tests pass
3. Run linters and formatters
4. Update documentation
5. Submit PR with clear description

---

**Current Status:** Phase 1 Complete ✅ - Ready for Phase 2 development
