---
name: weekly-review
description: Use when user wants to conduct weekly review, mentions "weekly review", "review my week", or needs to assess weekly progress.
---

# Weekly Review Skill

**Purpose:** Weekly tactical review focused on task triage, draft cleanup, and domain balance.

**Duration:** 30-45 minutes

**Key Principle:** The most important part of weekly review is ensuring your tasks reflect your actual priorities and that drafts don't pile up unreviewed.

---

## Entry Point — Incomplete Review Check

Before starting, check for an incomplete review already in progress.

Call `ziggy_get_review_state` with type `"weekly"`.

**If a review is in progress:**

```
Incomplete weekly review found (started [date]).
You must complete or discard the previous review before starting a new one.

Resume from where you left off? [Y]es / [D]iscard and restart
```

- If user says yes: resume from `current_step` in the saved state
- If user says discard: call `ziggy_clear_review_state` with type `"weekly"`, then start fresh

**Auto-upgrade to monthly check:**

Check today's date. If this is the first weekly review of a new month (i.e., no completed weekly review this month), redirect:

```
This is your first review of the month — upgrading to monthly review.
```

Then invoke the monthly-review skill instead of continuing here.

**Start the review:**

Call `ziggy_save_review_state` with:
- `type`: `"weekly"`
- `state`: `{"type": "weekly", "status": "in_progress", "current_step": "task_triage", "data": {}}`

Say: **"Starting weekly review. Let's see where things stand."**

---

## Section 1: Task Triage

**Purpose:** Surface incomplete and overdue tasks, group by domain, decide what to do with each.

### Step 1: Load Tasks

Call `ziggy_list_tasks` with no filters to get all tasks.

Group tasks into two buckets:

1. **Needs attention:** status is `inbox` or `active`
2. **Done this week:** status is `done` (for context — show count only)

Within "needs attention," group by domain: `home`, `health`, `personal`, `family`, `work`, `finances`, `social`.

Within each domain, sort by priority: URGENT first, then HIGH, MEDIUM, LOW.

### Step 2: Present Overview

Display a grouped summary:

```
Task Triage — Weekly Review

[Home] (3 tasks)
  URGENT: Fix leaking pipe under sink
  HIGH:   Schedule HVAC maintenance
  MEDIUM: Organize garage shelf

[Work] (5 tasks)
  HIGH:   Finish Q2 proposal (overdue)
  HIGH:   Review vendor contract
  MEDIUM: Send follow-up to client
  MEDIUM: Update project tracker
  LOW:    Read new policy document

[Health] (1 task)
  MEDIUM: Schedule annual physical

---
Total: 9 tasks needing attention
Done this week: 4 tasks
```

Flag any tasks that appear overdue (have a due date in the past) with "(overdue)".

### Step 3: Triage Each Domain

Work through each domain that has tasks. For each task, ask what happened:

```
[Work] — Finish Q2 proposal (overdue)
Priority: HIGH

What happened with this one?
1. Done — mark complete
2. Reschedule — still active, keep it
3. Reprioritize — change priority level
4. Delete — no longer needed
5. Skip — come back to it
```

Based on response:

| Choice | Action |
|--------|--------|
| Done | Call `ziggy_update_task` with `status: "done"` |
| Reschedule | Call `ziggy_update_task` with updated `due_date` if provided |
| Reprioritize | Ask for new priority, call `ziggy_update_task` with new `priority` |
| Delete | Call `ziggy_update_task` with `status: "deleted"` |
| Skip | Move on, no change |

**Batch mode for clean domains:** If a domain has all MEDIUM/LOW tasks and none are overdue, offer:

```
[Home] — 3 medium/low tasks, none overdue.
Keep all as-is? [Y]es / [N]o, review each
```

If yes, skip to next domain.

### Step 4: Mark Section Complete

Call `ziggy_save_review_state` with:
- `type`: `"weekly"`
- `state`: `{"type": "weekly", "status": "in_progress", "current_step": "draft_review", "data": {"tasks_triaged": true}}`

---

## Section 2: Draft Review

**Purpose:** Process pending drafts — flesh them out, promote to active, convert type, or delete.

### Step 1: Load Drafts

Call `ziggy_list_drafts` with no filters to get all drafts.

Also call `ziggy_list_drafts` with `type: "commitment"` to get commitment drafts specifically, since commitments are stored as drafts in the plugin.

Group drafts by type: `task`, `project`, `commitment`, `routine`, `goal`.

### Step 2: Present Overview

```
Drafts to Review

Projects (2 drafts):
  • Reorganize garage (from brain dump 3 days ago)
  • Plan family vacation (from brain dump 1 week ago)

Commitments (1 draft):
  • Exercise 3x/week (commitment draft)

Total: 3 drafts
```

If no drafts: "No drafts to review. Moving on."

### Step 3: Review Each Draft

For each draft, present:

```
Draft [type]: [title]
Created: [date]
Original: [description]

What would you like to do?
1. Flesh out now — add details and promote to active
2. Promote as-is — good enough, move to active
3. Convert type — change to task/project/commitment
4. Delete — not needed
5. Skip — review later
```

Based on response:

| Choice | Action |
|--------|--------|
| Flesh out | Ask follow-up questions (domain, priority, details), then call `ziggy_update_task` or relevant update tool with fleshed-out data and `status: "active"` |
| Promote as-is | Call `ziggy_update_task` with `status: "active"` |
| Convert | Ask what type, then store new item via `ziggy_store_task` or `ziggy_store_draft`, delete original |
| Delete | Call `ziggy_update_task` with `status: "deleted"` |
| Skip | No change, move on |

**Flesh-out prompts by type:**

For **project drafts**, ask:
- "What's the first concrete step?"
- "What domain is this? [home/health/personal/family/work/finances/social]"
- "How urgent is this? [urgent/high/medium/low]"

For **commitment drafts**, ask:
- "What's the target frequency? (e.g., 3x/week, daily, weekly)"
- "What domain does this belong to?"
- "How will you track this?"

### Step 4: Mark Section Complete

Call `ziggy_save_review_state` with:
- `type`: `"weekly"`
- `state`: `{"type": "weekly", "status": "in_progress", "current_step": "domain_balance", "data": {"tasks_triaged": true, "drafts_reviewed": true}}`

---

## Section 3: Domain Balance Check

**Purpose:** Compare your active task distribution against your stated values. Catch misalignment before it compounds.

### Step 1: Load Foundation

Call `ziggy_get_foundation` to read foundation pillars, especially the values/priorities section.

Also call `ziggy_list_tasks` to get all active tasks (you may already have this from Section 1).

### Step 2: Calculate Domain Distribution

Count active tasks per domain:

```
Active Tasks by Domain:

  home:     3 tasks
  work:     5 tasks  ← most active
  health:   1 task
  family:   0 tasks  ← none
  personal: 0 tasks  ← none
  finances: 1 task
  social:   0 tasks  ← none
```

### Step 3: Compare Against Values

Read the foundation to identify the user's top-priority domains (from stated values/priorities).

Common value-to-domain mappings:
- Family / relationships → `family`
- Health / fitness → `health`
- Financial stability → `finances`, `work`
- Personal growth → `personal`
- Community → `social`
- Home / environment → `home`

Identify **priority domains** — those tied to top values.

Flag any priority domains with zero active tasks:

```
Domain Balance Check

Your stated priorities suggest these domains matter most:
  → family (top value: family connection)
  → health (top value: wellbeing)

Current task load:
  family:  0 tasks  ← gap
  health:  1 task   ✓

Potential alignment gap: No active tasks in "family."
```

Then ask:

```
Does this reflect where you want to be putting your energy?

1. Yes, intentional (seasonal focus elsewhere)
2. No — I should add something in [domain]
3. My values have shifted — let's update foundation later
```

If the user wants to add a task in an underserved domain, capture it now via `ziggy_store_task` or `ziggy_store_draft`.

If no gaps are found:

```
Domain Balance: Work distribution aligns with stated values.
```

### Step 4: Mark Section Complete

Call `ziggy_save_review_state` with:
- `type`: `"weekly"`
- `state`: `{"type": "weekly", "status": "in_progress", "current_step": "summary", "data": {"tasks_triaged": true, "drafts_reviewed": true, "domain_balance_checked": true}}`

---

## Summary

Wrap up the review and show a summary of what was accomplished.

Display:

```
Weekly Review Complete!

This week:
  Tasks triaged: [N] tasks reviewed
    • [N] marked done
    • [N] rescheduled
    • [N] reprioritized
    • [N] deleted

  Drafts processed: [N] drafts reviewed
    • [N] promoted to active
    • [N] deleted
    • [N] skipped for later

  Domain balance: [aligned / gap in family, health]

Next review: [date 7 days from now]
```

Call `ziggy_clear_review_state` with type `"weekly"` to mark the review complete.

---

## Resuming an Interrupted Review

If the user resumes a review from a saved state, read `current_step` and jump to the appropriate section:

| current_step | Resume at |
|---|---|
| `task_triage` | Section 1 |
| `draft_review` | Section 2 |
| `domain_balance` | Section 3 |
| `summary` | Summary |

---

## MCP Tool Reference

| Action | Tool | Parameters |
|--------|------|------------|
| Check review state | `ziggy_get_review_state` | `type: "weekly"` |
| Save review progress | `ziggy_save_review_state` | `type: "weekly"`, `state: {...}` |
| Clear completed review | `ziggy_clear_review_state` | `type: "weekly"` |
| List all tasks | `ziggy_list_tasks` | optional: `status`, `domain`, `priority` |
| List drafts | `ziggy_list_drafts` | optional: `type` |
| Update a task | `ziggy_update_task` | `id`, and fields to update |
| Store new task | `ziggy_store_task` | `title`, `analysis`, optional `description`, `due_date` |
| Store draft | `ziggy_store_draft` | `title`, `type`, `analysis`, optional `description` |
| Read foundation | `ziggy_get_foundation` | (no parameters) |
| Get config | `ziggy_get_config` | (no parameters) |

---

## Key Principles

1. **Triage before planning** — Clear the slate before thinking about what's next
2. **Domains reveal priorities** — Task distribution is a mirror of actual behavior
3. **Drafts are technical debt** — Review them weekly or they pile up
4. **Ask, don't assume** — For each task disposition, ask the user; don't auto-reschedule
5. **Resume-safe** — Save state after each section so interrupted reviews can resume
6. **Keep it moving** — Offer batch approval for clean domains; don't force per-task review when it's not needed
