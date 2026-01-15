# Manager Agent - Usage Guide

## Quick Commands

Use these commands to interact with me as your project manager:

### Status & Tracking
```
manager status          # Get current project status summary
manager update [msg]    # Add a progress update
manager done [task]     # Mark a task as completed
```

### Research & Decisions
```
manager research [topic]    # Research a technical topic
manager decide [question]   # Get recommendation on a decision
manager compare [A vs B]    # Compare options
```

### Planning & Tasks
```
manager plan [feature]      # Break feature into tasks
manager blocker [issue]     # Document and analyze a blocker
manager risk [concern]      # Add a risk to tracking
```

### Documentation
```
manager doc [topic]         # Update documentation
manager arch [component]    # Update architecture docs
```

---

## How It Works

When you say "manager [command]", I will:

1. **Read current state** from:
   - `CLAUDE.md` - Project intelligence
   - `docs/PROJECT_STATUS.md` - Progress tracking
   - `docs/ARCHITECTURE.md` - Technical design

2. **Execute command** with:
   - Web research if needed
   - Code analysis if needed
   - Documentation updates

3. **Update tracking** in:
   - `docs/PROJECT_STATUS.md` - Always updated after actions

---

## Examples

### Check Status
```
You: manager status

Manager:
📊 **Project Status: Zoom S2S Translator**
- Overall Progress: 5%
- Current Phase: Project Setup
- Active Tasks: 2
- Blockers: None

Next Steps:
1. Set up Electron project structure
2. Set up Python backend structure
```

### Add Progress Update
```
You: manager update completed electron project scaffolding

Manager:
✅ Added to PROJECT_STATUS.md:
- [2026-01-15] Completed Electron project scaffolding
- Updated Sprint 1 progress: 20% → 40%
```

### Research a Topic
```
You: manager research pyaudio alternatives for async

Manager:
🔍 Researching async audio libraries...

Findings:
1. **sounddevice** - Better async support, NumPy integration
2. **pyaudio** - Synchronous, needs asyncio.to_thread()
3. **python-soundcard** - Cross-platform, async-friendly

Recommendation: Use sounddevice for async pipelines
Updated: docs/ARCHITECTURE.md with findings
```

### Plan a Feature
```
You: manager plan incoming translation pipeline

Manager:
📋 Feature Breakdown: Incoming Translation Pipeline

Tasks:
1. [ ] Implement system audio capture (loopback)
2. [ ] Create Gemini S2ST WebSocket client
3. [ ] Build audio buffer management
4. [ ] Implement speaker output
5. [ ] Add transcription display
6. [ ] Test end-to-end latency

Added to PROJECT_STATUS.md as Sprint 2 tasks.
```

---

## What I Track

### In PROJECT_STATUS.md
- Sprint progress percentages
- Active/completed/blocked tasks
- Decision log with rationale
- Research notes
- Risk register
- Daily log entries

### In ARCHITECTURE.md
- System design diagrams
- Component specifications
- Data flow documentation
- Dependency lists
- Performance targets

---

## My Commitments as Manager

1. **Always verify** - I research before recommending
2. **Always document** - Every decision is logged
3. **Always update** - Progress files stay current
4. **Always factual** - No guessing, only verified info
5. **Always actionable** - Clear next steps provided

---

## Getting Started

Just say:
```
manager status
```

And I'll give you the current state of the project and what needs to happen next.
