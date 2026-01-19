# Agent Orchestration Protocol

> This document defines the hierarchical agent orchestration system for the Zoom S2S Translator project.

## Overview

The orchestration system ensures structured communication between agents with clear ownership and responsibilities.

```
User
  │
  ▼
┌─────────────────────────┐
│    Project Manager      │  ← Single point of contact for users
│   (Green)               │  ← Owns: docs, decisions, user communication
└───────────┬─────────────┘
            │ writes to TASK_QUEUE.md
            ▼
┌─────────────────────────┐
│   Senior Developer      │  ← Technical lead
│   (Blue)                │  ← Owns: planning, review, commits
└───────────┬─────────────┘
            │ writes to JUNIOR_DEV_PLAN.md
            ▼
┌─────────────────────────┐
│   Junior Developer      │  ← Implementation specialist
│   (Cyan)                │  ← Owns: implementation, testing
└───────────┬─────────────┘
            │ writes to CODE_REVIEW_QUEUE.md
            └──────────────► (back to Senior Developer)
```

## Communication Channels

| Channel | From | To | Purpose |
|---------|------|-----|---------|
| `docs/TASK_QUEUE.md` | Project Manager | Senior Developer | Task delegation |
| `docs/JUNIOR_DEV_PLAN.md` | Senior Developer | Junior Developer | Implementation specs |
| `docs/CODE_REVIEW_QUEUE.md` | Junior Developer | Senior Developer | Code submission |
| `docs/PROJECT_STATUS.md` | All agents | User (via PM) | Progress tracking |

## Agent Responsibilities

### Project Manager (Green)

**Primary Role:** User interface and documentation owner

**Responsibilities:**
- Receive ALL user requests
- Make non-technical decisions independently
- Delegate technical work to Senior Developer
- Update PROJECT_STATUS.md with progress
- Close tasks and report to user

**Does NOT:**
- Write code
- Make architectural decisions
- Skip to junior developer directly

### Senior Developer (Blue)

**Primary Role:** Technical lead and quality gatekeeper

**Responsibilities:**
- Monitor TASK_QUEUE.md for new tasks
- Analyze requirements and plan implementations
- Create detailed specs in JUNIOR_DEV_PLAN.md
- Review code from Junior Developer
- Commit approved code
- Report completion back to TASK_QUEUE.md

**Does NOT:**
- Communicate directly with users
- Update PROJECT_STATUS.md (that's PM's job)
- Implement features (that's Junior's job)

### Junior Developer (Cyan)

**Primary Role:** Implementation specialist

**Responsibilities:**
- Read tasks from JUNIOR_DEV_PLAN.md
- Implement EXACTLY what is specified
- Write tests as specified
- Submit work to CODE_REVIEW_QUEUE.md
- Address review feedback

**Does NOT:**
- Make architectural decisions
- Commit code directly
- Skip the review process
- Communicate directly with users

## Workflow Lifecycle

### Phase 1: Task Creation
1. User makes request to Project Manager
2. PM acknowledges request
3. PM creates task in `TASK_QUEUE.md` with status `pending_senior_review`
4. PM informs user: "Task created, assigned to Senior Developer"

### Phase 2: Planning
1. Senior Developer picks up task from `TASK_QUEUE.md`
2. Updates status to `in_progress_senior`
3. Analyzes requirements, researches best practices
4. Creates detailed implementation plan in `JUNIOR_DEV_PLAN.md`
5. Updates `TASK_QUEUE.md` status to `pending_implementation`

### Phase 3: Implementation
1. Junior Developer reads task from `JUNIOR_DEV_PLAN.md`
2. Studies existing patterns as instructed
3. Implements code following specifications
4. Writes tests as specified
5. Submits to `CODE_REVIEW_QUEUE.md` with status `pending_review`
6. Updates `JUNIOR_DEV_PLAN.md` task to `submitted_for_review`

### Phase 4: Review & Commit
1. Senior Developer reviews submission in `CODE_REVIEW_QUEUE.md`
2. If approved:
   - Commits code to repository
   - Updates `CODE_REVIEW_QUEUE.md` to `committed`
   - Updates `TASK_QUEUE.md` to `completed`
3. If changes needed:
   - Updates `CODE_REVIEW_QUEUE.md` to `changes_requested` with feedback
   - Junior Developer addresses feedback and resubmits

### Phase 5: Closure
1. Project Manager sees `completed` status in `TASK_QUEUE.md`
2. Verifies acceptance criteria met
3. Updates `PROJECT_STATUS.md`
4. Marks task as `closed`
5. Reports to user

## Escalation Protocol

### Junior Developer Blockers
If Junior Developer encounters:
- Unclear requirements
- Architectural decisions needed
- Technical blockers

**Action:**
1. Flag in `CODE_REVIEW_QUEUE.md` with `needs_clarification`
2. Describe the blocker clearly
3. Wait for Senior Developer guidance
4. NEVER make assumptions about architecture

### Senior Developer Blockers
If Senior Developer encounters:
- Scope creep
- Requirements ambiguity
- Resource constraints

**Action:**
1. Update `TASK_QUEUE.md` with blocker note
2. Flag for Project Manager attention
3. Wait for PM to clarify with user

### Critical Issues
For security vulnerabilities, data loss risks, or critical bugs:

**Action:**
1. Immediate notification up the chain
2. Mark as `CRITICAL` in relevant queue
3. All other work paused until resolved

## Bypass Commands

Users can bypass the hierarchy in exceptional cases:

| Command | Effect |
|---------|--------|
| `/senior [request]` | Direct access to Senior Developer |
| `/junior [request]` | Direct access to Junior Developer |

**Note:** Bypass should be rare. The hierarchy exists for quality control.

## File Locations

```
zoom-client-s2s-translator/
├── docs/
│   ├── TASK_QUEUE.md           # PM → Senior communication
│   ├── CODE_REVIEW_QUEUE.md    # Junior → Senior communication
│   ├── JUNIOR_DEV_PLAN.md      # Senior → Junior communication
│   ├── PROJECT_STATUS.md       # Progress tracking
│   ├── ARCHITECTURE.md         # Technical design
│   └── ORCHESTRATION_PROTOCOL.md  # This file
├── CLAUDE.md                   # Project intelligence
└── .claude/agents/
    ├── project-manager.md
    ├── senior-developer.md
    └── junior-developer.md
```

## Status Codes Summary

### TASK_QUEUE.md
- `pending_senior_review` → `in_progress_senior` → `pending_implementation` → `in_implementation` → `pending_code_review` → `completed` → `closed`

### CODE_REVIEW_QUEUE.md
- `pending_review` → `in_review` → `approved` / `changes_requested` → `committed`

### JUNIOR_DEV_PLAN.md
- `ready_for_implementation` → `in_progress` → `submitted_for_review` → `completed`

## Best Practices

1. **Always update status** - Stale queues cause confusion
2. **Be explicit** - Over-communicate rather than under-communicate
3. **Respect the hierarchy** - It exists for quality control
4. **Document decisions** - Future agents need context
5. **Keep queues clean** - Archive completed items regularly
