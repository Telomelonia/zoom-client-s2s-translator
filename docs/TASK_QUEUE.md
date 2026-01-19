# Task Queue

> Communication channel between Project Manager and Senior Developer

## How This Works

1. **Project Manager** creates tasks here when user requests require code changes
2. **Senior Developer** monitors this queue for pending tasks
3. Tasks flow through the status lifecycle until completion
4. Once completed, **Project Manager** closes tasks and updates documentation

## Active Tasks

_No active tasks_

## Task Status Legend

| Status | Description |
|--------|-------------|
| `pending_senior_review` | Waiting for Senior Developer to pick up |
| `in_progress_senior` | Senior Developer is planning/analyzing |
| `pending_implementation` | Plan ready, waiting for Junior Developer |
| `in_implementation` | Junior Developer working on it |
| `pending_code_review` | Code submitted, awaiting Senior review |
| `completed` | Done - PM to update docs and close |
| `closed` | Fully complete |

## Task Template

When creating a new task, copy this template:

```markdown
### TASK-YYYY-MM-DD-NNN: [Short Title]

| Field | Value |
|-------|-------|
| **ID** | TASK-YYYY-MM-DD-NNN |
| **Status** | pending_senior_review |
| **Created** | YYYY-MM-DD |
| **Created By** | @project-manager |
| **Assigned To** | @senior-developer |
| **Priority** | High / Medium / Low |

**Description:**
[Detailed description of what needs to be done]

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

**Context/Background:**
[Any relevant context from user request or project status]

**Files Likely Affected:**
- `path/to/file1`
- `path/to/file2`

---

**Senior Developer Notes:**
_To be filled by Senior Developer during planning_

**Implementation Plan Link:**
_Link to JUNIOR_DEV_PLAN.md entry once created_

**Completion Notes:**
_To be filled when task is completed_

| Commit Hash | Files Changed | Completed Date |
|-------------|---------------|----------------|
| | | |
```

---

## Completed Tasks Archive

_Completed tasks are moved here after closure_

---

## Queue Management Rules

1. **One task at a time per developer** - Don't overload the queue
2. **Priority ordering** - Critical > High > Medium > Low
3. **Dependencies noted** - If Task B depends on Task A, note it clearly
4. **Status updates required** - Update status when transitioning
5. **Blockers escalated** - If blocked, mark status and notify PM
