---
name: capture
description: Use when user has messy tasks/ideas to organize, says "brain dump", mentions multiple todos, or needs to capture scattered thoughts.
---

# Brain Dump / Capture

**Purpose:** Convert natural language brain dumps into organized local tasks and drafts.

**Mode:** Production (creates real tasks via `ziggy_store_task`, drafts via `ziggy_store_draft`)

---

## Step 1: Greet and Detect Mode

Say: **"Ready for a brain dump! Tell me what's on your mind - tasks, ideas, things to do, whatever's floating around."**

**Two modes:**
- **Interactive (default):** User talks, you process in real-time
- **File shortcut:** If user provides a file path, read it and process

---

## Step 1.5: Analyze Each Item with ziggy_analyze

**CRITICAL:** Use the `ziggy_analyze` MCP tool for ALL classification. Do NOT use keyword-only matching.

Call `ziggy_analyze` with the user's text. The tool returns an analysis object:

```
{
  "is_clear_task": true/false,
  "entity_detection": {
    "type": "task" | "project" | "goal" | "commitment" | "routine" | "initiative",
    "confidence": 0.0-1.0,
    "signals": ["deadline approaching", "blocking others", ...],
    "explanation": "Detected as task based on: ..."
  },
  "priority": {
    "score": 0.0-1.0,
    "level": "URGENT" | "HIGH" | "MEDIUM" | "LOW",
    "signals": ["deadline approaching", "time-sensitive", ...]
  },
  "domain": {
    "matched": "home" | "health" | "personal" | "family" | "work" | "finances" | "social",
    "confidence": "high" | "medium" | "low",
    "keywords_found": ["keyword1", "keyword2"]
  },
  "owner": {
    "suggested": "John" | "Kristen" | "Both",
    "reason": "work domain default",
    "needs_clarification": true/false
  },
  "duration": 30  // estimated minutes, or null
}
```

Use these results for ALL routing decisions, not keyword matching.

---

## Step 1.6: Entity Quick-Learn Flow

After analyzing each item, process entity mentions to resolve known entities and learn about unknown ones.

### Phase 1: Bucket Entity Mentions

Call `ziggy_detect_mentions` with the item text. This returns a list of detected entity mentions. For each mention, call `ziggy_resolve_entity` with the mention text (and optional `context_domain`):

- Status `resolved` → entity is known, use it
- Status `fuzzy_match` → close match found (e.g., "maria" → "Maria Chen"), treat as known
- Status `ambiguous` → multiple matches, note candidates for later clarification
- Status `unknown` → no match found, candidate for quick-learn

### Phase 2: Triage Unknown Entities

Bucket unknown entities by their triage score (returned by `ziggy_analyze`):

| Triage Score | Action |
|--------------|--------|
| **>= 3** | Ask now (high priority) - user likely needs to reference this entity again |
| **1-2** | Create stub entity, queue for later enrichment |

### Phase 3: Quick-Learn Prompt

For high-priority unknowns (triage score >= 3), batch ask the user:

```
I spotted some names/places I don't know yet. Quick context?

1. **Maria** (mentioned in "Call Maria about taxes")
   → Who is Maria? (one line)

2. **138A Classon** (mentioned in "Check on 138A Classon repairs")
   → What is this? (one line)

[Type answers, or "skip" to create stubs for later]
```

### Phase 4: Create Entities from Responses

For each response, call `ziggy_create_entity` with:
- `name`: entity name
- `type`: inferred entity type
- `subtype`: inferred subtype
- `domain`: domain from analysis
- `aliases`: common aliases or role references

**Entity Type Inference:**
- Names → `person` (subtype: `professional`, `family`, `friend`)
- Addresses → `place` (subtype: `property`, `business`)
- Companies → `organization`

### Quick Mode Escape Hatch

If user says "skip" or "just capture":
1. Create stub entities with `enrichment_status: stub` via `ziggy_create_entity`
2. Continue with capture flow without blocking

---

## Step 2: Parse and Classify Items

As user provides input, extract individual items. For EACH item:

1. Call `ziggy_analyze` with the item text
2. Check `entity_detection.type`:
   - `task` → Likely a task (check `is_clear_task`)
   - `project` → Needs clarification or project draft
   - `goal` → Needs goal draft
   - `commitment` → Needs commitment draft
   - `routine` → Needs routine draft
   - `initiative` → Needs initiative draft
3. If informational (no action verb, "learned that", "idea:") → SKIP (no notes in plugin v1)

### Entity Type Routing

| Analysis Result | Action |
|-----------------|--------|
| `is_clear_task=true` | Store task immediately via `ziggy_store_task` |
| `is_clear_task=false`, `type=task` | Ask clarification or create draft via `ziggy_store_draft` |
| `type=project/goal/commitment/routine` | Ask clarification, route to draft |
| Informational only (no action signals) | Acknowledge and skip (PKM out of scope in plugin v1) |

---

## Step 2.5: Clarification Flow for Ambiguous Items

When `is_clear_task=false` or entity type is not `task`, ask the user.

### Ambiguity Detection

An item needs clarification when:
- `entity_detection.type` is `project`, `goal`, `commitment`, or `initiative`
- `entity_detection.confidence` < 0.7 AND signals only include `default_case`
- Text starts with ambiguous verbs: "plan", "organize", "figure out", "work on", "look into"

### Clarification Prompt

Present to user:

```
"[item text]"

This could be:
1. **Quick Task** - Single action, do it and done
2. **Project** - Multiple steps, needs planning
3. **Commitment** - Recurring behavior change
4. **Skip** - Not actionable right now

Which is it? [1/2/3/4]
```

### Based on Response

| Response | Action |
|----------|--------|
| 1 (Task) | Store task via `ziggy_store_task` with service-derived priority/domain |
| 2 (Project) | Store draft via `ziggy_store_draft` with type `project` |
| 3 (Commitment) | Store draft via `ziggy_store_draft` with type `commitment` |
| 4 (Skip) | Acknowledge and move to next item |

### Draft Format

The `ziggy_store_draft` tool accepts:
- `title`: item text
- `type`: `"project"` | `"commitment"` | `"goal"` | `"routine"`
- `analysis`: full analysis result (JSON)
- `description`: optional additional context

---

## Step 3A: Process TASKS (→ local storage)

For each clear task (`is_clear_task=true`), use the analysis results:

### Priority (from ziggy_analyze)

The tool calculates priority using multiple factors:

| Factor | Score Contribution |
|--------|-------------------|
| Deadline within 2 days | +0.8 |
| Blocking others | +0.6 |
| Seasonal constraint ("before winter") | +0.5 |
| Time-sensitive ("running low", "closes") | +0.4 |

| Total Score | Priority Level |
|-------------|----------------|
| >= 0.6 | URGENT |
| >= 0.3 | HIGH |
| >= 0.1 | MEDIUM |
| < 0.1 | MEDIUM |

**Always use `analysis["priority"]["level"]`** - do not re-derive from keywords.

Show user: "Priority: {level} (signals: {signals})"

### Domain (from ziggy_analyze)

The tool matches domain based on keyword scoring:

| Domain | Example Keywords |
|--------|------------------|
| **Home** | house, garage, garden, maintenance, repair, organize |
| **Health** | doctor, fitness, exercise, medical, therapy, wellness |
| **Personal** | learn, read, hobby, skill, practice, creative |
| **Family** | kids, spouse, school, vacation, birthday |
| **Work** | client, project, meeting, deadline, team, business |
| **Finances** | money, budget, bank, tax, investment, bill |
| **Social** | friends, community, church, volunteer, party |

**Always use `analysis["domain"]["matched"]`** with confidence level.

### Owner Suggestion

The tool suggests an owner based on domain defaults:

| Domain | Default Owner |
|--------|--------------|
| home | John |
| health | Both |
| personal | Both |
| family | Both |
| work | John |
| finances | John |
| social | Both |

When `owner.needs_clarification=true` (owner is "Both"):

```
Owner: This could be for John or Kristen. Who should own it?
[J]ohn / [K]risten / [B]oth
```

If user doesn't specify, default to the suggested owner.

### Big Task Breakdown (>30 minutes)

When `analysis["duration"] > 30`:

```
This task seems substantial (~{duration} min estimate).

Would you like me to break it into subtasks?
[Y]es / [N]o, keep as single task
```

If Yes:
1. Ask user for 2-4 subtasks
2. Store parent task via `ziggy_store_task` with subtasks included
3. Or suggest subtasks based on the task description

Example breakdown:
- "Update pricing model" (60 min) ->
  - "Review current pricing structure" (15 min)
  - "Research competitor pricing" (20 min)
  - "Draft new pricing proposal" (25 min)

### Store the Task

Call `ziggy_store_task` with:
- `title`: task title
- `analysis`: full analysis result (JSON)
- `description`: optional additional context
- `due_date`: optional due date if detected

---

## Step 4: Handle Mixed Input

Brain dumps often contain both tasks and non-task items:

**User says:**
> "talked to vendor about pricing - they're raising rates 15%. Need to update our pricing model by end of month. Idea: maybe lock in a longer contract."

**You extract:**
1. **SKIP**: "talked to vendor about pricing - they're raising rates 15%"
   - Informational only, no action verb
   - Acknowledge: "Got it (noted, but PKM capture not active in this version)"

2. **TASK**: "update our pricing model by end of month"
   - Domain: Work
   - Priority: High (deadline)
   - Estimate: 60m
   - → Stored via `ziggy_store_task`

3. **SKIP**: "Idea: maybe lock in a longer contract"
   - Informational / fleeting idea
   - Acknowledge as noted

---

## Step 5: Confirmation

After processing, show detailed summary:

```
Captured 5 items:

TASKS:
+ Update pricing model
  Domain: Work | Priority: HIGH (deadline approaching)
  Owner: John
  Duration: 60 min -> Broken into 3 subtasks

+ Call procurement about contract
  Domain: Work | Priority: MEDIUM
  Owner: John | Standalone task

DRAFTS (review later):
~ "Reorganize garage" -> Project draft
   Needs: planning, breakdown

SKIPPED:
- "Maybe look into new CRM" -> User chose to skip
- "Talked to vendor..." -> Informational (no PKM in plugin v1)

---
Tasks: 2 stored, 1 draft
```

---

## Error Handling

- If `ziggy_store_task` fails: Show error, continue with other items
- If `ziggy_store_draft` fails: Show error, continue with other items
- At end, summarize: "Stored 4/5 items. 1 failed."

---

## Examples

### Example 1: Mixed brain dump with clarification

**User:** "Need to update our integration by Friday. Also figure out the garage situation."

**Analysis results:**
1. "update our integration by Friday" → `is_clear_task=true`, priority=HIGH (deadline)
2. "figure out the garage situation" → `is_clear_task=false`, type=project (ambiguous verb)

**You process:**

1. TASK: Update integration (store immediately via `ziggy_store_task`)
   - Domain: Work
   - Priority: HIGH (deadline Friday)
   - Owner: John

2. CLARIFICATION NEEDED: "figure out the garage situation"
   ```
   "Figure out the garage situation"

   This could be:
   1. Quick Task - Single action
   2. Project - Multiple steps, needs planning
   3. Skip

   Which is it?
   ```

   User: "2" (Project)
   -> Stored draft via `ziggy_store_draft` with type `project`

### Example 2: Owner clarification

**User:** "Schedule violin lessons for Ariadne"

**Analysis:**
- is_clear_task: true
- domain: Family
- owner: { suggested: "Both", needs_clarification: true }

**You ask:**
```
Owner: This could be for John or Kristen. Who should own it?
[J]ohn / [K]risten
```

User: "K"
-> Stored task assigned to Kristen

### Example 3: Big task breakdown

**User:** "Reorganize the entire garage, will probably take a full day"

**Analysis:**
- is_clear_task: true
- duration: 480 (full day)
- domain: Home

**You ask:**
```
This task seems substantial (~480 min estimate).

Would you like me to break it into subtasks?
[Y]es / [N]o
```

User: "Y"

**You suggest:**
```
Suggested breakdown:
1. Clear out and sort items (2 hours)
2. Install shelving/organization (2 hours)
3. Put everything back organized (2 hours)
4. Dispose of unwanted items (2 hours)

Look good? [Y]es / [E]dit
```

---

## Key Principles

1. **Use ziggy_analyze for ALL analysis** - Never rely on keyword-only matching
2. **Ask, don't guess** - When ambiguous, ask user to clarify (task vs project vs commitment)
3. **Show your work** - Display priority signals, domain confidence, owner reasoning
4. **Clear tasks go to local storage immediately** - Only `is_clear_task=true` items
5. **Ambiguous items become drafts** - Stored via `ziggy_store_draft` for later review
6. **Big tasks get breakdown offers** - >30 min estimate triggers subtask suggestion
7. **No PKM in plugin v1** - Informational items are acknowledged but not stored; skip gracefully
8. **Desktop has richer interaction** - More per-item confirmation than mobile
