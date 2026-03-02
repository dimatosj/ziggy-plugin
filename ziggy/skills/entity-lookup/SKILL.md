---
name: entity-lookup
description: Use when user asks about an entity, mentions "what do I know about X", wants to see entity details, or references a known person/place/thing.
---

# Entity Lookup

**Purpose:** Surface full entity context when user asks about a known entity.

**Triggers:**
- "What do I know about [entity]?"
- "Tell me about [entity]"
- "Show me [entity]"
- "[Entity] status"
- "Who is [entity]?"
- "What is [entity]?"

---

## Step 1: Resolve Entity

Call the `ziggy_resolve_entity` MCP tool with the user's query to resolve the entity. The tool returns:
- `status`: One of "resolved", "ambiguous", "fuzzy_match", or "unknown"
- `entity`: The resolved entity object (if resolved)
- `candidates`: List of possible matches (if ambiguous)

**Handle each status:**

### Resolved
The entity was found with certainty. Proceed to Step 2.

### Ambiguous
Multiple entities match. Present numbered options and ask user to clarify:

> "I found multiple matches:
> 1. Maria Papadopoulos (accountant, finances)
> 2. Maria Garcia (contractor, home)
>
> Which one did you mean?"

### Fuzzy Match
Only a close match was found (e.g., "maria" → "Maria Chen"):

> "Did you mean **Maria Chen** (your accountant)?
>
> [Say yes or no]"

If user confirms, proceed. If not, check if they want to create a new entity.

### Unknown
The entity is not in the knowledge base.

> "I don't have any information about that. Would you like to create an entity profile for [name]?"

---

## Step 2: Gather Entity Context

For the resolved entity, gather context using the data returned by `ziggy_resolve_entity`.

The entity object includes:
- `name`: Entity name
- `type`: person, property, or organization
- `subtype`: Specific subtype (e.g., professional, family, friend)
- `domain`: Domain (e.g., finances, home, health, work)
- `description`: Full profile content
- `contact_info`: Email, phone, address (if available)
- `aliases`: Known aliases or nicknames
- `relationships`: Links to related entities

**Gather related entities:** For each relationship, call `ziggy_resolve_entity` with the related entity name to get their details.

---

## Step 3: Present Context

Format and present the entity information clearly:

```
## [Entity Name]

**Type:** [type] ([subtype])
**Domain:** [domain]

### Profile

[Description content from entity]

### Contact Info

[Phone, email, address as available]
[If none, note "No contact info recorded"]

### Aliases

[List of known aliases/nicknames, if any]

### Related Entities

[If relationships exist, list them]
- **[Name]** ([type], [relationship type])
```

---

## Step 4: Offer Quick Actions

After presenting context, offer relevant actions based on entity type:

### For Person entities:
> **Quick Actions:**
> 1. Add task mentioning [name]
> 2. Update contact info
> 3. See related entities

### For Property entities:
> **Quick Actions:**
> 1. Add task for [property]
> 2. See related contacts
> 3. Update property info

### For Organization entities:
> **Quick Actions:**
> 1. Add task mentioning [org]
> 2. See related people
> 3. Update organization info

Ask: "What would you like to do?"

---

## Creating a New Entity

If the user wants to create an entity (either during resolution for an unknown entity, or after confirming they want to create a new one):

1. **Ask for entity type:**
   > "Is this a person, property, or organization?"

2. **Gather key details:**
   - Entity type (person, property, organization)
   - Entity name
   - Subtype (e.g., professional, family, owned, rental, school, company)
   - Domain (home, health, personal, family, work, finances, social)
   - Brief description
   - Aliases (if any)
   - Contact info (email/phone for professionals)

3. **Call the MCP tool:**

Call `ziggy_create_entity` with:
- `name`: Full name
- `entity_type`: person, property, or organization
- `subtype`: Specific subtype
- `domain`: Primary domain
- `description`: Profile content
- `aliases`: List of known aliases (optional)
- `contact_email`: Email (optional)
- `contact_phone`: Phone (optional)

4. **Confirm creation:**

> "Perfect! I've created an entity profile for [name]. You can reference them anytime by asking 'who is [name]?'"

---

## Error Handling

### Entity Not Found
If `ziggy_resolve_entity` returns "unknown" status:
- Ask if they want to create a new entity profile
- If yes, proceed with entity creation flow
- If no, offer help finding similar entities

### Resolve Tool Failure
If the `ziggy_resolve_entity` tool call fails:
- Acknowledge: "I hit a hiccup looking that up. Let me try again."
- Retry the tool call
- If it persists, explain: "I'm having trouble accessing the entity database. Try again in a moment."

### Create Tool Failure
If the `ziggy_create_entity` tool call fails:
- Acknowledge: "I had trouble saving that. Let me try again."
- Retry with the same parameters
- If it continues to fail, note: "I'm having trouble saving the profile. Try again in a moment, or provide the info again to retry."

---

## Complete Flow Example

**User:** "Who is Maria?"

**Step 1: Resolve**
- Call `ziggy_resolve_entity` with query "Maria"
- Returns: status = "fuzzy_match", entity = {name: "Maria Chen", ...}

**Step 2-3: Confirm and Present**
- "Did you mean **Maria Chen** (accountant, finances)?"
- User confirms
- Display: Name, type, domain, profile, contact info, aliases, related entities

**Step 4: Offer Actions**
- "Quick actions: Add task mentioning Maria, Update contact info, See related entities"

**User:** "Add task mentioning Maria"
- (Delegates to capture skill to create a task)

---

## Notes on Resolution

- **Exact matches** are resolved immediately (status = "resolved")
- **Fuzzy matches** happen when a partial name or alias is provided (status = "fuzzy_match")
- **Ambiguous matches** occur when multiple entities could fit the query (status = "ambiguous")
- **Unknown** means the entity doesn't exist and user is asked to create one

The `ziggy_resolve_entity` tool handles all of this internally using:
- Entity index for fast exact and fuzzy matching
- Entity profiles for full context
- Relationship detection for related entities

---

## Success Criteria

The skill succeeds when:
1. Entity is successfully resolved or created
2. User sees full context (profile, contact info, relationships)
3. User can take quick actions (add task, update info, etc.)
4. If unknown, user can create a new entity profile
5. All MCP tool calls are properly formatted and executed
