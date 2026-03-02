---
name: monthly-review
description: Use when user wants to conduct monthly review, mentions "monthly review", or needs strategic + tactical review.
---

# Monthly Review Skill

**Purpose:** Monthly strategic + tactical review. Includes ALL of weekly review PLUS monthly-specific items.

**Duration:** 60-90 minutes

**Structure:** Weekly review (complete) + Monthly extras

---

## Entry Point — Incomplete Review Check

Before starting, check for an incomplete review already in progress.

Call `ziggy_get_review_state` with type `"monthly"`.

**If a review is in progress:**

```
Incomplete monthly review found (started [date]).
You must complete or discard the previous review before starting a new one.

Resume from where you left off? [Y]es / [D]iscard and restart
```

- If user says yes: resume from `current_step` in the saved state
- If user says discard: call `ziggy_clear_review_state` with type `"monthly"`, then start fresh

**Start the review:**

Call `ziggy_save_review_state` with:
- `type`: `"monthly"`
- `state`: `{"type": "monthly", "status": "in_progress", "current_step": "task_triage", "data": {}}`

Say: **"Starting monthly review. This includes your full weekly review plus monthly extras."**

---

## Sections 1–3: Weekly Review Flow

Sections 1 through 3 follow the same flow as the weekly review skill:

1. **Section 1: Task Triage** — Load all tasks, group by domain, triage each
2. **Section 2: Draft Review** — Process all pending drafts
3. **Section 3: Domain Balance Check** — Compare task distribution against foundation values

Refer to the weekly-review skill for the detailed steps in each of these sections.

After completing each weekly-review section, save state with type `"monthly"` (not `"weekly"`) so progress is tracked under the monthly review. Use:

```
current_step values:
  "task_triage"        → after entry
  "draft_review"       → after Section 1 complete
  "domain_balance"     → after Section 2 complete
  "monthly_commitments" → after Section 3 complete
  "all_drafts_review"  → after Section 4 complete
  "capacity_assessment" → after Section 5 complete
  "summary"            → all sections complete
```

Do NOT auto-upgrade to another review type during monthly review. Skip the auto-upgrade check from the weekly-review skill entry point.

---

## Section 4: Active Commitments (Monthly Check)

**Purpose:** Monthly check-in on established commitments. Focus on trends over the month, not single-week performance.

### Step 1: Load Commitment Drafts

Call `ziggy_list_drafts` with `type: "commitment"` to get all commitment drafts.

Identify **established commitments**: those created more than 60 days ago. These are reviewed at the monthly cadence rather than weekly.

### Step 2: Present Commitment Overview

```
Section 4: Active Commitments — Monthly Check

Established commitments (60+ days old):
  • Exercise 3x/week [health] — active 4 months
  • Weekly family dinner [family] — active 3 months
  • Daily journaling [personal] — active 2 months

Total: 3 commitments at monthly cadence
```

If no established commitments:

```
No commitments at monthly cadence yet.
All active commitments are new (under 60 days) and reviewed weekly.
Moving on.
```

### Step 3: Monthly Check-In Per Commitment

For each established commitment:

```
[Commitment]: Exercise 3x/week
Domain: health
How has this been going this month overall?
(Think about the trend, not just last week)
```

Wait for user response describing the monthly trend.

Then ask:

```
Any adjustments needed, or keep going?

1. Keep going — no change
2. Adjust — change frequency or target
3. Deactivate — temporarily pause
4. Archive — no longer relevant
```

Based on response:

| Choice | Action |
|--------|--------|
| Keep going | Call `ziggy_update_task` with `id` to update `last_reviewed` or add a note |
| Adjust | Ask what changes, then call `ziggy_update_task` with updated details |
| Deactivate | Call `ziggy_update_task` with `status: "inactive"` |
| Archive | Call `ziggy_update_task` with `status: "deleted"` |

### Step 4: Mark Section Complete

Call `ziggy_save_review_state` with:
- `type`: `"monthly"`
- `state`: `{"type": "monthly", "status": "in_progress", "current_step": "all_drafts_review", "data": {"tasks_triaged": true, "drafts_reviewed": true, "domain_balance_checked": true, "commitments_reviewed": true}}`

---

## Section 5: All Drafts — Expanded Review

**Purpose:** At the monthly cadence, review ALL draft types comprehensively — not just the quick pass from Section 2. This is the time to flesh out drafts that were skipped during weekly reviews.

### Step 1: Load All Drafts

Call `ziggy_list_drafts` with no filter to get all drafts across all types.

Group by type:

```
All Drafts — Monthly Review

Tasks (3 drafts):
  • [title] — [age]
  • ...

Projects (2 drafts):
  • [title] — [age]
  • ...

Commitments (1 draft):
  • [title] — [age]

Routines (1 draft):
  • [title] — [age]

Goals (0 drafts)
```

If no drafts at all:

```
No drafts pending. Nothing to review here.
```

### Step 2: Triage by Age

Flag any draft older than 30 days as **stale**:

```
Stale drafts (30+ days old):
  • Plan garage reorganization [project] — 45 days old
  • Start a book club [personal] — 38 days old

These have been sitting a while. Time to decide.
```

### Step 3: Review Each Draft

Work through each draft. Present:

```
[Type]: [title]
Created: [date] ([age])
Description: [description or "no description"]
```

For stale drafts (30+ days), add a nudge:

```
This draft is [N] days old. Has it been on your mind?
```

Then ask:

```
What would you like to do?
1. Flesh out now — add details and promote to active
2. Promote as-is — good enough, move to active
3. Convert type — change to a different type
4. Keep as draft — not ready yet
5. Delete — not needed
```

| Choice | Action |
|--------|--------|
| Flesh out | Ask follow-up questions, then call `ziggy_update_task` or `ziggy_store_draft` with full details, set `status: "active"` |
| Promote as-is | Call `ziggy_update_task` with `status: "active"` |
| Convert | Ask target type, store new item via appropriate tool, delete original |
| Keep as draft | No change — but note if it's been kept for 2+ months in a row |
| Delete | Call `ziggy_update_task` with `status: "deleted"` |

**Monthly note:** At the monthly cadence, push harder on stale drafts. If a draft has been sitting for 60+ days, prompt:

```
This draft is 60+ days old. If it hasn't been acted on, it may not be a real priority.
Delete it and re-capture later if it comes back to mind?
[Y]es, delete / [N]o, keep
```

### Step 4: Mark Section Complete

Call `ziggy_save_review_state` with:
- `type`: `"monthly"`
- `state`: `{"type": "monthly", "status": "in_progress", "current_step": "capacity_assessment", "data": {"tasks_triaged": true, "drafts_reviewed": true, "domain_balance_checked": true, "commitments_reviewed": true, "all_drafts_reviewed": true}}`

---

## Section 6: Capacity Assessment

**Purpose:** Foundation-aware bandwidth check to prevent overcommitment. Compare your current task and draft load against your stated capacity in the foundation.

**When to run:** Run this section at every monthly review. It is brief if no concerns are present.

### Step 1: Load Data

Call `ziggy_get_foundation` to read foundation pillars.

Call `ziggy_list_tasks` to count active tasks by domain (you may already have this from Section 1).

Call `ziggy_list_drafts` to count pending drafts (you may already have this from Section 5).

### Step 2: Present Capacity Overview

```
Section 6: Capacity Assessment

Current load:
  Active tasks:    [N] tasks
  Pending drafts:  [N] drafts
  Total items:     [N]
```

### Step 3: Read Foundation for Capacity Signals

From the foundation pillars, look for any mention of:
- Current bandwidth or capacity constraints
- Seasonal pressures (busy periods, travel, major projects at work)
- Life context notes (health issues, family obligations, etc.)

Present what you find:

```
From your foundation:
  life-context: "[relevant notes about current life season]"
  values/priorities: "[any capacity or bandwidth notes]"
```

If the foundation has no relevant capacity notes:

```
Your foundation doesn't have specific capacity notes for this period.
```

### Step 4: Provide Assessment

Based on the task and draft counts against foundation context, give a brief assessment:

```
Capacity Assessment:

You have [N] active tasks and [N] drafts pending.

[If heavy load with constrained foundation notes]:
  Your foundation notes suggest constrained bandwidth right now.
  With [N] active tasks, you may be overcommitted.
  Consider: archiving low-priority tasks or drafts, or holding off on
  promoting more drafts to active.

[If light load with available bandwidth notes]:
  You have bandwidth available. If there are priorities you've been
  deferring, now may be a good time to pick them up.

[If load seems aligned]:
  Your current load appears well-matched to your stated capacity.
```

Then ask:

```
Any capacity concerns to discuss?

1. No — looks good
2. Yes — let's talk through it
```

If the user wants to discuss, engage in a brief coaching conversation. Use the foundation context to ground the conversation.

### Step 5: Mark Section Complete

Call `ziggy_save_review_state` with:
- `type`: `"monthly"`
- `state`: `{"type": "monthly", "status": "in_progress", "current_step": "summary", "data": {"tasks_triaged": true, "drafts_reviewed": true, "domain_balance_checked": true, "commitments_reviewed": true, "all_drafts_reviewed": true, "capacity_assessed": true}}`

---

## Summary

Wrap up and display a full summary of the monthly review.

```
Monthly Review Complete!

Weekly Review:
  Tasks triaged: [N] tasks reviewed
    • [N] marked done
    • [N] rescheduled
    • [N] reprioritized
    • [N] deleted

  Drafts reviewed: [N] quick-pass drafts
    • [N] promoted to active
    • [N] deleted

  Domain balance: [aligned / gap in family, health]

Monthly Extras:
  Commitments reviewed: [N] established commitments
    • [N] kept going
    • [N] adjusted
    • [N] archived

  All drafts reviewed: [N] total drafts
    • [N] promoted to active
    • [N] deleted
    • [N] kept as draft

  Capacity: [aligned / concerns discussed]

Next review: [date 7 days from now (weekly)]
Next monthly review: [date ~30 days from now]
```

Call `ziggy_clear_review_state` with type `"monthly"` to mark the review complete.

---

## Edge Cases

### Auto-Upgraded from Weekly

If the user invoked the weekly-review skill and was redirected here because it's the first review of the month:

```
This is your first review of the month — upgrading to monthly review.

This will include:
  • Full weekly review (task triage, draft review, domain balance)
  • Monthly commitment check-in
  • Expanded draft review across all types
  • Capacity assessment

Ready to proceed? [Y]es / [N]o
```

### User Invokes Monthly Mid-Month

If the user already completed a review this month, acknowledge it:

```
You completed a review earlier this month (on [date]).

This monthly review will still include the full scope.
Continue? [Y]es / [N]o
```

### No Established Commitments

If all commitments are new (under 60 days):

```
Section 4: Active Commitments — Monthly Check

All your active commitments are recent (under 60 days old) and
are reviewed at weekly cadence. Nothing to add here.
```

---

## Resuming an Interrupted Review

If the user resumes from a saved state, read `current_step` and jump to the appropriate section:

| current_step | Resume at |
|---|---|
| `task_triage` | Section 1 |
| `draft_review` | Section 2 |
| `domain_balance` | Section 3 |
| `monthly_commitments` | Section 4 |
| `all_drafts_review` | Section 5 |
| `capacity_assessment` | Section 6 |
| `summary` | Summary |

---

## MCP Tool Reference

| Action | Tool | Parameters |
|--------|------|------------|
| Check review state | `ziggy_get_review_state` | `type: "monthly"` |
| Save review progress | `ziggy_save_review_state` | `type: "monthly"`, `state: {...}` |
| Clear completed review | `ziggy_clear_review_state` | `type: "monthly"` |
| List all tasks | `ziggy_list_tasks` | optional: `status`, `domain`, `priority` |
| List drafts | `ziggy_list_drafts` | optional: `type` |
| List commitment drafts | `ziggy_list_drafts` | `type: "commitment"` |
| Update a task or draft | `ziggy_update_task` | `id`, and fields to update |
| Store new task | `ziggy_store_task` | `title`, `analysis`, optional `description`, `due_date` |
| Store draft | `ziggy_store_draft` | `title`, `type`, `analysis`, optional `description` |
| Read foundation | `ziggy_get_foundation` | (no parameters) |
| Get config | `ziggy_get_config` | (no parameters) |

---

## Key Principles

1. **Monthly = weekly + extras** — Don't skip the weekly review sections; they're the foundation
2. **Established commitments need monthly perspective** — Trends matter more than single-week performance
3. **Stale drafts are decisions deferred** — Monthly is the time to force a decision on aging drafts
4. **Capacity check grounds everything** — Always close the loop with foundation context
5. **Resume-safe** — Save state after each section; monthly reviews often take multiple sittings
6. **Don't batch too aggressively** — Monthly cadence warrants more deliberate review than weekly
