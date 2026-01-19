# Code Review Queue

> Communication channel between Junior Developer and Senior Developer

## How This Works

1. **Junior Developer** submits completed work here after implementation
2. **Senior Developer** reviews submissions and provides feedback
3. If approved, Senior Developer commits the code
4. If changes needed, Junior Developer addresses feedback and resubmits

## Pending Reviews

_No pending reviews_

## Review Status Legend

| Status | Description |
|--------|-------------|
| `pending_review` | Awaiting Senior Developer review |
| `in_review` | Senior Developer actively reviewing |
| `approved` | Approved - will be committed |
| `changes_requested` | Feedback provided - needs revision |
| `committed` | Code committed to repository |

## Review Request Template

When submitting for review, copy this template:

```markdown
### REVIEW-YYYY-MM-DD-NNN: [Short Description]

| Field | Value |
|-------|-------|
| **Review ID** | REVIEW-YYYY-MM-DD-NNN |
| **Task ID** | TASK-XXX (from TASK_QUEUE.md) |
| **Status** | pending_review |
| **Submitted** | YYYY-MM-DD HH:MM |
| **Submitted By** | @junior-developer |
| **Reviewer** | @senior-developer |

**Summary of Changes:**
[Brief description of what was implemented]

**Files Changed:**
| File | Change Type | Description |
|------|-------------|-------------|
| `path/to/file1.ts` | Added | New component for X |
| `path/to/file2.py` | Modified | Added Y functionality |
| `path/to/file3.ts` | Modified | Fixed Z issue |

**Implementation Notes:**
- Note about design decision 1
- Note about pattern followed
- Any deviations from plan (with justification)

**Testing Done:**
- [ ] Unit tests written and passing
- [ ] Manual testing performed
- [ ] Edge cases covered

**Self-Review Checklist:**
- [ ] Code compiles/runs without errors
- [ ] No debug statements left in code
- [ ] Error handling is comprehensive
- [ ] Types are explicit (no 'any')
- [ ] Follows existing project patterns
- [ ] Public APIs documented

**Questions for Reviewer:**
- Any specific areas you'd like feedback on

---

**Review Feedback:**
_To be filled by Senior Developer_

**Review Decision:** `pending_review`

**Required Changes:**
_If changes_requested, list specific changes needed_

**Commit Info:**
_If approved_
| Commit Hash | Branch | Date |
|-------------|--------|------|
| | | |
```

---

## Completed Reviews Archive

_Completed reviews are moved here after commit_

---

## Review Guidelines

### For Junior Developer (Submitting)
1. **Complete the checklist** - Don't submit incomplete work
2. **Be detailed** - More context = faster review
3. **Flag uncertainties** - Ask questions proactively
4. **Test thoroughly** - Don't rely on review to catch bugs

### For Senior Developer (Reviewing)
1. **Timely reviews** - Don't let submissions sit
2. **Constructive feedback** - Explain the "why"
3. **Prioritize issues** - Critical > Important > Suggestions
4. **Acknowledge good work** - Positive reinforcement matters

### Review Criteria
- Correctness and logic
- Error handling
- Security considerations
- Performance implications
- Code style and maintainability
- Test coverage
- Documentation
