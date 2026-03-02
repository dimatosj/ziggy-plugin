---
name: daily-start
description: Use when starting a new day or session, says "start my day", "morning check", or needs to see what's pending.
---

# Daily Start Skill

Quick status check at the start of a day or session.

## Trigger Patterns

- "start my day"
- "morning check"
- "what's pending?"
- Beginning of session

---

## Overview

The daily-start skill surfaces what matters today: task urgency, entity follow-ups due, and pending reviews. It uses MCP tools to fetch live data and presents a clear action menu.

---

## Step 1: Show Today's Date

Display the current date for context:

> **Today:** Sunday, March 2, 2026

---

## Step 2: Task Summary by Priority

Call `ziggy_list_tasks` with no filters to fetch all tasks. The tool returns a list of tasks with status, priority, domain, and description.

**Display logic:**

1. Filter for status `inbox` or `active` (tasks that need attention)
2. Group by priority: URGENT, HIGH, MEDIUM, LOW
3. For each priority group with tasks, show:
   - Priority level
   - Count of tasks at that level
   - Top 2-3 task titles (brief)
   - If more than 3, show count of remaining

**Example output:**

```
Task Summary:

URGENT (2 tasks):
  • Call Maria about tax returns
  • Submit expense report (due today)
  → 2 urgent tasks pending

HIGH (4 tasks):
  • Finish Q1 planning
  • Review vendor proposal
  → Show 2 more...

MEDIUM (6 tasks)
  • Grocery shopping
  → 6 medium priority tasks

Total: 12 tasks inbox/active
```

**If no urgent/high tasks:** Skip those sections silently, show only populated priorities.

**If no tasks at all:** "No pending tasks. You're all clear!"

---

## Step 3: Entity Alerts

Call `ziggy_list_entities` with no filters to fetch all entities. The tool returns entity name, type, subtype, domain, and last contact date.

**Check for alerts:**

1. **Stub entities** (enrichment_status = "stub") → "Entity needs enrichment"
2. **Overdue contacts** (person type, last_contact > 30 days ago) → "Contact follow-up due"

**Display logic:**

Group alerts by type and show summary:

```
Entity Alerts:

Stub entities needing enrichment:
  • Maria (accountant, not yet profiled)
  • 138A Classon (property, needs details)

Overdue contacts (> 30 days):
  • Dr. Rodriguez (pediatrician) — 45 days since contact
  • Aunt Linda — 60 days since contact
```

**If no alerts:** Skip this section silently.

---

## Step 4: Pending Reviews

Call `ziggy_get_review_state` for each review type: `weekly`, `monthly`, `quarterly`.

The tool returns the review status: `pending`, `in-progress`, or `completed`.

**Display logic:**

Show only reviews that are `pending` or `in-progress`:

```
Pending Reviews:

Weekly Review:
  → In progress (started yesterday)

Monthly Review:
  → Pending (due by end of month)
```

**If no pending reviews:** "No pending reviews."

---

## Step 5: Action Menu

Offer quick-access actions:

```
What would you like to do?

1. Capture tasks (/capture)
2. Review a task in detail
3. Check an entity
4. Start weekly review
5. Just get to work
```

---

## Example Full Output

```
Daily Start — Sunday, March 2, 2026

Task Summary:

URGENT (2 tasks):
  • Call Maria about tax returns
  • Submit expense report (due today)

HIGH (3 tasks):
  • Finish Q1 planning
  • Review vendor proposal
  → 1 more...

MEDIUM (6 tasks)
  • Grocery shopping
  → 6 medium priority tasks

Total: 12 tasks inbox/active

---

Entity Alerts:

Stub entities needing enrichment:
  • Maria (accountant, not yet profiled)

Overdue contacts (> 30 days):
  • Dr. Rodriguez (pediatrician) — 45 days since contact

---

Pending Reviews:

Weekly Review:
  → In progress (started yesterday)

---

What would you like to do?

1. Capture tasks (/capture)
2. Review a task in detail
3. Check an entity
4. Start weekly review
5. Just get to work
```

---

## MCP Tools Reference

| Action | Tool | Notes |
|--------|------|-------|
| List tasks | `ziggy_list_tasks` | Optional filters: status, domain, priority |
| List entities | `ziggy_list_entities` | Optional filters: type, domain |
| Get reviews | `ziggy_get_review_state` | Takes review type: weekly/monthly/quarterly |

---

## Key Principles

1. **Quick scan** — This is a 30-second status check, not a deep review
2. **Show urgency first** — URGENT and HIGH tasks get top visibility
3. **Surface attention items** — Stub entities and overdue contacts are actionable
4. **Offer next steps** — Action menu guides user to relevant skills
5. **Skip silently** — If no alerts/reviews/tasks in a category, don't display empty sections
