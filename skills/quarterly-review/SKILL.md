---
name: quarterly-review
description: Use when user wants to conduct quarterly review, mentions "quarterly review", "Q1 review", or needs strategic reflection.
---

# Quarterly Review Skill

**Purpose:** Deep strategic reflection and forward planning. Step back from daily/weekly execution and assess whether your energy is going toward what matters most.

**Duration:** 90-120 minutes

**Key Activities:**
1. **Reflect** on the previous quarter — what happened, what worked, what didn't
2. **Review tasks and drafts** — archive completed work, triage stale items
3. **Update foundation** — review and revise your foundation pillars
4. **Plan next quarter** — set priorities and direction going forward

**Timing:** Typically the last week of the current quarter, before the new quarter starts.

---

## Entry Point — Timing and Setup

Before starting, check for an incomplete review.

Call `ziggy_get_review_state` with type `"quarterly"`.

**If a review is in progress:**

```
Incomplete quarterly review found (started [date]).
Resume from where you left off? [Y]es / [D]iscard and restart
```

- If yes: resume from `current_step`
- If discard: call `ziggy_clear_review_state` with type `"quarterly"`, then start fresh

**Determine the quarter:**

Ask the user which quarter they are reviewing. Suggest the quarter that just ended based on today's date.

```
Which quarter are we reviewing?

Today is [date]. Suggested: [Q] [year]
(Type the quarter, e.g. "Q1 2026", or press Enter to accept)
```

Wait for user to confirm or specify a different quarter. Store as `quarter` and `year` throughout this skill.

Determine the next quarter (for planning section):
- Q1 → Q2 (same year)
- Q2 → Q3 (same year)
- Q3 → Q4 (same year)
- Q4 → Q1 (next year)

**Start the review:**

Call `ziggy_save_review_state` with:
- `type`: `"quarterly"`
- `state`: `{"type": "quarterly", "status": "in_progress", "current_step": "quarter_reflection", "quarter": "[Q]", "year": [year], "data": {}}`

Say:

```
Starting Quarterly Review: [Q] [year]

This review has 4 sections:
  1. Quarter Reflection — what happened, what worked, what didn't
  2. Task & Draft Review — triage all items, archive completed work
  3. Foundation Update — review and revise your foundation pillars
  4. Next Quarter Planning — set priorities and direction

Let's begin.
```

---

## Section 1: Quarter Reflection

**Purpose:** Deep, honest reflection on the quarter that just passed. This is not task triage — it's a strategic conversation about meaning, patterns, and lessons.

### Step 1: Open Reflection

Call `ziggy_get_foundation` to read the foundation pillars. This gives context for what the user was aiming toward this quarter.

Look specifically for any notes about:
- Goals or intentions for this quarter
- Life context or season notes
- Values that were being prioritized

Present brief context:

```
Section 1: Quarter Reflection — [Q] [year]

From your foundation, heading into this quarter:
  [Relevant excerpt from foundation, or "No specific notes found for this quarter."]

Let's reflect on how it actually went.
```

### Step 2: Guided Reflection Questions

Work through these reflection questions one at a time. Ask each, wait for the user's response, then proceed to the next.

**Question 1 — Big picture:**

```
Looking back at [Q] [year] as a whole:
What were the big wins? What are you most proud of?
```

**Question 2 — Challenges:**

```
What were the biggest challenges or frustrations this quarter?
What slowed you down or didn't go as planned?
```

**Question 3 — Patterns:**

```
What patterns do you notice?
(Things that kept coming up, recurring obstacles, or themes in how you worked)
```

**Question 4 — Energy and focus:**

```
Where did your energy actually go this quarter?
Was it where you intended to put it?
```

**Question 5 — Key lessons:**

```
What's the most important thing you're taking away from this quarter?
```

After all five responses, offer a brief synthesis:

```
Reflection Summary for [Q] [year]:

  Wins: [brief summary of what user said]
  Challenges: [brief summary]
  Key lesson: [brief summary]

Does this feel accurate? Anything to add or correct?
```

Store the full reflection in the review state. Call `ziggy_save_review_state` with:
- `type`: `"quarterly"`
- `state`: current state with reflection responses added to `data`

### Step 3: Mark Section Complete

Call `ziggy_save_review_state` with `current_step: "task_draft_review"`.

---

## Section 2: Task & Draft Review

**Purpose:** Comprehensive triage of all tasks and drafts. Archive completed work, clear stale items, and surface anything that still needs attention.

### Step 1: Load All Tasks and Drafts

Call `ziggy_list_tasks` with no filters to get all tasks.

Call `ziggy_list_drafts` with no filters to get all drafts.

### Step 2: Task Triage

Group tasks by status:

```
Section 2: Task & Draft Review

Tasks:
  Done (completed work):     [N] tasks
  Active (still in progress): [N] tasks
  Inbox (uncategorized):     [N] tasks
  Stale (no update in 60+ days): [N] tasks
```

**For completed tasks (done):**

```
You have [N] completed tasks this quarter.
Archive all completed tasks? [Y]es / [R]eview each first
```

If yes: call `ziggy_update_task` with `status: "archived"` for each done task (batch).
If review: show each and confirm before archiving.

**For stale tasks (active/inbox with no recent activity):**

Flag any task that has been active or in inbox for 60+ days without being updated as stale.

For each stale task:

```
Stale task (60+ days inactive): [title]
Priority: [priority] | Domain: [domain]

Still relevant?
1. Yes — keep active
2. Reprioritize — change priority
3. Delete — no longer needed
4. Archive — done but wasn't marked
```

**For active tasks:**

Offer a batch review option:

```
You have [N] active tasks still in progress.
Bulk review? [Y]es, show all / [N]o, skip (continue to drafts)
```

If yes, show each active task and confirm it should remain active. Allow reprioritizing or deleting.

### Step 3: Draft Triage

For all drafts:

```
Drafts:
  By type:
    tasks:       [N]
    projects:    [N]
    commitments: [N]
    routines:    [N]
    goals:       [N]
```

At the quarterly cadence, any draft older than 90 days is considered very stale:

```
Very stale drafts (90+ days):
  • [title] [type] — [age]
```

For each draft, present:

```
[Type]: [title]
Created: [date] ([age])

1. Flesh out and promote to active
2. Keep as draft
3. Delete
```

Push for decisions on stale drafts. If a draft is 90+ days old:

```
This draft is [N] days old — three months without action.
Consider deleting unless it's genuinely still a priority.
```

### Step 4: Mark Section Complete

Call `ziggy_save_review_state` with `current_step: "foundation_update"` and updated data object tracking triage counts.

---

## Section 3: Foundation Update

**Purpose:** The foundation represents your life context, values, and priorities. The quarterly review is the right time to update it — not just read it, but revise it to reflect who you are now and what matters going into the next quarter.

### Step 1: Load and Present Foundation

Call `ziggy_get_foundation` to read all foundation pillars.

Present each pillar:

```
Section 3: Foundation Update

Your current foundation pillars:

[Pillar name]
---
[Current content]
---
```

Display each pillar in turn.

### Step 2: Review Each Pillar

For each pillar, ask:

```
[Pillar name]: Does this still reflect your current situation and priorities?

1. Yes — no changes needed
2. Minor update — small edits
3. Major revision — significant rewrite
4. I'd like to discuss — talk through what should change
```

If the user wants to update (minor or major), ask them to describe the changes they want. You can ask follow-up questions to draw out specifics.

Then call `ziggy_update_foundation` with:
- `pillar`: the pillar name
- `content`: the updated content

Confirm after each update:

```
Foundation updated: [pillar name]
```

**Common pillars to review:**

- **life-context:** Current life season, major circumstances, upcoming changes
- **values:** What matters most, non-negotiables
- **priorities:** Focus areas for this period
- **household-capability:** Available bandwidth, constraints

**Guiding questions if the user is unsure what to update:**

- "Has anything significant changed in your life this quarter?"
- "Are there new constraints or freed-up time you should capture?"
- "Do your stated values still feel right, or have your priorities shifted?"
- "What would you want to remember about this life season a year from now?"

### Step 3: Mark Section Complete

Call `ziggy_save_review_state` with `current_step: "next_quarter_planning"` and note foundation was updated.

---

## Section 4: Next Quarter Planning

**Purpose:** Set clear intentions and priorities for the upcoming quarter. This is forward-looking — based on your reflection, your updated foundation, and what you want to accomplish.

### Step 1: Load Context

Call `ziggy_list_tasks` to see current active tasks.
Call `ziggy_list_drafts` to see any remaining drafts.
Call `ziggy_get_foundation` (may already be loaded from Section 3).

### Step 2: Open Planning Conversation

Summarize what you know from the previous sections:

```
Section 4: Next Quarter Planning — [next_quarter] [next_year]

From your reflection:
  Key lesson: [from Section 1]

Current state going into [next_quarter]:
  Active tasks: [N]
  Pending drafts: [N]
  Foundation: [recently updated / up to date]
```

### Step 3: Priority Setting

Ask the user to think about the next quarter at a high level:

```
Looking ahead to [next_quarter] [next_year]:

What are your top 2-3 priorities for this quarter?
(These should reflect your foundation values and what you want to accomplish)
```

Wait for user response. This might be:
- Specific projects or outcomes they want to achieve
- Areas of life they want to focus on
- Habits or commitments they want to establish
- Problems they want to solve

### Step 4: Translate Priorities to Concrete Items

For each priority the user names, help them translate it into concrete items:

```
Priority: [user's stated priority]

How would you like to track progress on this?
1. Create a task — specific, completable action
2. Create a draft project — for multi-step work
3. Create a draft commitment — for ongoing habits
4. Just note it — capture as a foundation note for now
```

Based on response:

| Choice | Action |
|--------|--------|
| Create task | Call `ziggy_store_task` with title and analysis |
| Draft project | Call `ziggy_store_draft` with `type: "project"` |
| Draft commitment | Call `ziggy_store_draft` with `type: "commitment"` |
| Note it | Offer to call `ziggy_update_foundation` to add a note to the relevant pillar |

### Step 5: Capacity Check

Before closing, do a quick check:

```
You're heading into [next_quarter] with:
  [N] active tasks
  [N] drafts to process
  [N] new items just created

From your foundation: [relevant bandwidth/capacity notes]

Does this feel manageable for [next_quarter]?

1. Yes — ready to go
2. Too much — let's trim something
3. Could do more — let's add something
```

If the user wants to trim, guide them back to deleting or deprioritizing tasks.
If the user wants to add more, ask what area and help them create an item.

### Step 6: Mark Section Complete

Call `ziggy_save_review_state` with `current_step: "summary"`.

---

## Summary

Display the full quarterly review summary:

```
Quarterly Review Complete!

[Q] [year] Reflection:
  Wins: [brief summary]
  Challenges: [brief summary]
  Key lesson: [key lesson]

Task & Draft Review:
  Tasks archived: [N]
  Tasks deleted: [N]
  Drafts promoted: [N]
  Drafts deleted: [N]
  Active tasks remaining: [N]

Foundation:
  Pillars reviewed: [N]
  Pillars updated: [N or "No changes"]

[next_quarter] [next_year] Planning:
  New tasks created: [N]
  New drafts created: [N]
  Top priorities: [list what user named]

[next_quarter] starts: [date]
Next quarterly review: [Q after next_quarter], [year]
```

Call `ziggy_clear_review_state` with type `"quarterly"` to mark the review complete.

---

## Resuming an Interrupted Review

If the user resumes from a saved state, read `current_step` and jump to the appropriate section:

| current_step | Resume at |
|---|---|
| `quarter_reflection` | Section 1 |
| `task_draft_review` | Section 2 |
| `foundation_update` | Section 3 |
| `next_quarter_planning` | Section 4 |
| `summary` | Summary |

---

## MCP Tool Reference

| Action | Tool | Parameters |
|--------|------|------------|
| Check review state | `ziggy_get_review_state` | `type: "quarterly"` |
| Save review progress | `ziggy_save_review_state` | `type: "quarterly"`, `state: {...}` |
| Clear completed review | `ziggy_clear_review_state` | `type: "quarterly"` |
| List all tasks | `ziggy_list_tasks` | optional: `status`, `domain`, `priority` |
| List all drafts | `ziggy_list_drafts` | optional: `type` |
| Update a task or draft | `ziggy_update_task` | `id`, and fields to update |
| Store new task | `ziggy_store_task` | `title`, `analysis`, optional `description`, `due_date` |
| Store draft | `ziggy_store_draft` | `title`, `type`, `analysis`, optional `description` |
| Read foundation | `ziggy_get_foundation` | (no parameters) |
| Update foundation pillar | `ziggy_update_foundation` | `pillar`, `content` |
| Get config | `ziggy_get_config` | (no parameters) |

---

## Key Principles

1. **This is strategic, not tactical** — Don't let the quarterly review become a task list review. Section 1 is the heart of it.
2. **Reflection before planning** — You cannot plan well without honest reflection. Don't rush to Section 4.
3. **Foundation is the anchor** — The foundation pillars connect daily tasks to life values. Update them carefully and honestly.
4. **Simplicity over taxonomy** — The plugin has no goals/initiatives/projects hierarchy. Use tasks and drafts as the primary vehicles for intention.
5. **Decisions, not deferral** — At the quarterly cadence, stale drafts and tasks should be resolved, not carried forward again.
6. **Resume-safe** — Quarterly reviews often span multiple sessions. Save state after each section.
7. **Ask, then synthesize** — Let the user's words drive the reflection. Your job is to hold the structure and synthesize, not to tell them what they experienced.
