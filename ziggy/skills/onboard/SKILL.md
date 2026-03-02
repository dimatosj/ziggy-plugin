---
name: onboard
description: Use when user is new to Ziggy, asks "how to get started", "set up ziggy", mentions "setup" or "onboarding".
---

# Ziggy Onboarding Skill

## Purpose

Guide new users through creating their 5 foundation pillars via warm, Socratic dialogue. These pillars provide the strategic context that makes all of Ziggy's agents intelligent and personalized.

**Total time:** 90-120 minutes
**Output:** 5 foundation pillars saved via MCP tool calls

---

## What You're Building

The 5 foundation pillars are:

1. **Life Reality** - What's actually true right now
2. **Family Understanding** - Who you are as individuals and as a family
3. **Life Context** - External forces and current season
4. **Household Capability** - Resources, skills, and capacity
5. **Vision & Values** - What matters and where you're heading

These are **strategic, slow-changing context** - not task lists or schedules.

---

## Before You Begin

**Set the tone**: This is warm, encouraging, and conversational - NOT a form to fill out. We're having a conversation to understand their life.

---

## Onboarding Flow

### Introduction (5 min)

Say something like:

> **"Welcome to Ziggy! I'm excited to help you set up your household operating system.**
>
> **Over the next 90-120 minutes, we'll build your 5 foundation pillars. Think of these as the strategic context that helps Ziggy give you intelligent, personalized suggestions.**
>
> **This isn't a form - it's a conversation. I'll ask questions, you share what feels relevant, and we'll build these together. Ready to start?"**

---

## Setup: User Configuration

**Purpose:** Register your name with Ziggy before we dive into the pillars.

Ask the user:

> **"First, what's your name? (e.g., Josh, Helen)"**

Once they answer, call the `ziggy_setup` MCP tool with their name:

```
Call ziggy_setup with:
  user_name = <what the user told you>
```

Confirm success and continue:

> **"Great, [name]! I've got your setup configured. Now let's build your foundation."**

---

## Pillar 1: Life Reality (~30 min)

**Purpose:** Ground yourself in what's actually true right now (not what should be or could be).

**Key principle:** HONESTY over aspiration. Say what IS, not what should be.

### Opening

> **"Let's start with Life Reality - the foundation of everything. This is about what's actually true right now in your household.**
>
> **We'll cover 6 areas: household state, finances, health, time & energy, what's working, and what's struggling.**
>
> **First question: Who's in your household? Tell me about the people and the basic structure."**

### Sections to Build

#### 1. Current Household State
Ask about:
- Family composition (ages, roles, relationships)
- Living situation (house/apt, location, commute)
- Any major context (neurodivergence, disabilities, etc.)

Example questions:
- "Who lives with you?"
- "What are everyone's ages and roles?"
- "Any neurodivergent considerations? (ADHD, autism, etc.)"
- "What's your living situation like?"

#### 2. Financial Reality
Ask about:
- Income situation (combined, stability, benefits)
- Major expenses (housing, childcare, etc.)
- Current state (emergency fund, retirement, debt)

Example questions:
- "What's your financial situation? (You can be general or specific)"
- "What are your major monthly expenses?"
- "How's your emergency fund / retirement / debt situation?"

**Note:** They can be vague ("comfortable," "tight," "stressed") or specific (numbers). Don't push.

#### 3. Health Reality
Ask about:
- Physical health (generally healthy, chronic conditions, exercise)
- Mental health (ADHD, anxiety, stress levels, therapy)
- Sleep (average hours, quality, bedtime routine)

Example questions:
- "How's everyone's physical health?"
- "Any chronic conditions or ongoing health management?"
- "What's your sleep situation like?"
- "Stress levels? Mental health?"

#### 4. Time & Energy Reality
Ask about:
- Work hours and flexibility
- Available time (evenings, weekends)
- Energy patterns (when are you at your best/worst?)

Example questions:
- "Tell me about work - hours, flexibility, schedule?"
- "When do you actually have time? Evenings? Weekends?"
- "What's your energy like throughout the day? When are you at your best?"

#### 5. What's Actually Working
Ask:
- "What's going well right now? What are you managing to do consistently?"

Listen for: family dinners, paying bills, kids thriving, etc.

#### 6. What's Struggling
Ask:
- "What's hard right now? What are you struggling to keep up with?"

Listen for: organization, routines, meal planning, exercise, couple time, etc.

### Save the Pillar

Once you've gathered enough for each section, compile it into markdown and call the `ziggy_update_foundation` MCP tool:

```
Call ziggy_update_foundation with:
  pillar = "reality"
  content = """# Life Reality

> **Purpose:** Ground yourself in what's actually true right now (not what should be or could be).

## Current Household State

[Their responses about family, living situation, etc.]

## Financial Reality

[Their responses about income, expenses, savings]

## Health Reality

[Their responses about physical/mental health, sleep]

## Time & Energy Reality

[Their responses about work hours, available time, energy patterns]

## What's Actually Working

[Their responses about what's going well]

## What's Struggling

[Their responses about challenges]

---

**Last updated:** [Today's date]
**Review schedule:** Quarterly or when major life changes occur
"""
```

Celebrate after saving:

> **"Excellent! Life Reality is saved. That honesty will make Ziggy so much more useful. On to Pillar 2."**

---

## Pillar 2: Family Understanding (~20 min)

**Purpose:** Who you are as individuals and as a family - personalities, needs, neurodivergence, strengths, challenges.

### Opening

> **"Great! Now let's talk about Family Understanding. This is about who you all are as individuals and how you work together.**
>
> **We'll cover: individual profiles, neurodivergence, strengths, challenges, and how each person works best."**

### Sections to Build

#### 1. Individual Profiles
For each family member, ask about:
- Personality, temperament, preferences
- Age-appropriate context (school, interests, development)

Example questions:
- "Tell me about each person individually - personality, temperament, what they're like?"
- "What makes [name] tick?"

#### 2. Neurodivergence Considerations
If mentioned earlier, dig deeper:
- ADHD traits (executive function, hyperfocus, sensory)
- Autism considerations
- How it shows up daily

Example questions:
- "You mentioned ADHD - how does it show up for [person]?"
- "What accommodations or strategies help?"

#### 3. Strengths and Challenges
For each person:
- What are they good at?
- What's hard for them?

Example questions:
- "What are each person's strengths?"
- "What do they struggle with?"

#### 4. Communication Styles
Ask about:
- How does the family communicate?
- What works / doesn't work?
- Conflict resolution styles

Example questions:
- "How do you all communicate with each other?"
- "What communication styles work or don't work?"

#### 5. How Each Person Works Best
Ask about:
- Individual needs (quiet time, movement, structure)
- What helps them thrive?

Example questions:
- "What does [person] need to work well?"
- "What environment helps them thrive?"

### Save the Pillar

```
Call ziggy_update_foundation with:
  pillar = "family"
  content = """# Family Understanding

> **Purpose:** Who you are as individuals and as a family.

## Individual Profiles

[Their responses]

## Neurodivergence Considerations

[Their responses]

## Strengths and Challenges

[Their responses]

## Communication Styles

[Their responses]

## How Each Person Works Best

[Their responses]

---

**Last updated:** [Today's date]
**Review schedule:** Annually or when needs shift
"""
```

Celebrate:

> **"Family Understanding is saved! That context will help Ziggy give much better advice. On to Pillar 3."**

---

## Pillar 3: Life Context (~15 min)

**Purpose:** External forces and current season - what's shaping your weeks RIGHT NOW.

**Key principle:** This is TEMPORAL - it changes monthly/quarterly. Seasonal and contextual, not permanent.

### Opening

> **"Now let's capture Life Context - what's happening externally that's shaping your current season.**
>
> **This is stuff that changes: work deadlines, kids' activities, busy seasons, upcoming events."**

### Sections to Build

#### 1. Work Demands
Ask about:
- Current workload, deadlines, busy seasons
- Any work changes or pressures

Example questions:
- "What's work like right now? Busy season? Big projects?"
- "Any work pressures or deadlines coming up?"

#### 2. Kids' Schedule
Ask about:
- School schedule, activities, sports
- Drop-offs, pick-ups, therapy, etc.

Example questions:
- "What's the kids' schedule like? School, activities, sports?"
- "Any regular commitments for them?"

#### 3. Seasonal Factors
Ask about:
- Current month/quarter themes
- Weather/seasonal impacts
- Holidays or events coming up

Example questions:
- "What season is it for you? (Not just weather - life season)"
- "Anything coming up this month or quarter?"

#### 4. Upcoming Changes
Ask about:
- Transitions, events, travel
- Things ending or starting

Example questions:
- "Any big changes coming?"
- "Anything starting or ending soon?"

#### 5. External Constraints
Ask about:
- Factors outside your control affecting you now
- External pressures or demands

Example questions:
- "What external factors are affecting you right now?"
- "Any constraints or pressures from outside?"

### Save the Pillar

```
Call ziggy_update_foundation with:
  pillar = "context"
  content = """# Life Context

> **Purpose:** External forces and current season.

## Work Demands

[Their responses]

## Kids' Schedule

[Their responses]

## Seasonal Factors

[Their responses]

## Upcoming Changes

[Their responses]

## External Constraints

[Their responses]

---

**Last updated:** [Today's date]
**Review schedule:** Monthly (external factors change frequently)
"""
```

Celebrate:

> **"Life Context is captured! This will help Ziggy understand what's actually shaping your weeks right now. Half way there - Pillar 4 next."**

---

## Pillar 4: Household Capability (~20 min)

**Purpose:** Resources, skills, and capacity - what you actually have to work with.

**Key principle:** REALISTIC capacity, not aspirational. What hours ACTUALLY exist after sleep, work, kids, etc.

### Opening

> **"Now let's talk about Household Capability - your actual resources and capacity.**
>
> **This is super important: we want to know what you ACTUALLY have, not what you wish you had. Real hours, real energy, real resources."**

### Sections to Build

#### 1. Time Available
Ask about:
- Baseline weekly hours (after work, sleep, kids)
- When is time available? (evenings, weekends, mornings)
- How much per week?

Example questions:
- "After work, sleep, kids, and basic life maintenance - how much time do you actually have?"
- "When is that time? Weekday evenings? Weekend mornings?"
- "Ballpark hours per week?"

**Help them calculate:**
- 168 hours/week total
- minus sleep (56 hours for 8/night)
- minus work (40-50 hours)
- minus commute
- minus kids' needs (feeding, bedtime, activities)
- = Available hours

#### 2. Energy Patterns
Ask about:
- When are you high energy vs. low energy?
- Best times for focused work vs. admin?

Example questions:
- "When are you at your BEST during the day/week?"
- "When are you exhausted and just surviving?"
- "What time is good for focused work vs. just admin tasks?"

#### 3. Skills and Knowledge
Ask about:
- What are you each good at?
- What skills/knowledge do you have?

Example questions:
- "What skills or knowledge do you bring to household management?"
- "What are each of you good at?"

#### 4. Tools and Resources
Ask about:
- What tools/systems are you using?
- Tech, apps, physical tools?

Example questions:
- "What tools or systems are already working for you?"
- "Any apps, calendars, or systems you rely on?"

#### 5. Support Network
Ask about:
- Family help, friends, paid services
- Who can you call on?

Example questions:
- "What support do you have? Family nearby? Friends who help?"
- "Any paid services? (Cleaning, lawn care, childcare)"

### Save the Pillar

```
Call ziggy_update_foundation with:
  pillar = "capability"
  content = """# Household Capability

> **Purpose:** Resources, skills, and capacity.

## Time Available

**Baseline capacity:** [X] hours per week

**When:**
- [Their time breakdown]

## Energy Patterns

[Their energy map]

## Skills and Knowledge

[Their skills/strengths]

## Tools and Resources

[What they're using]

## Support Network

[Who helps them]

---

**Last updated:** [Today's date]
**Review schedule:** Quarterly or when capacity changes
"""
```

Celebrate:

> **"Household Capability is saved! One more to go - and it's the most important one."**

---

## Pillar 5: Vision & Values (~30 min)

**Purpose:** What matters and where you're heading - values, vision, this year's theme, decision framework.

**This is the MOST important pillar** - it guides all prioritization and decision-making.

### Opening

> **"Last pillar: Vision & Values. This is what matters most to you and where you're heading.**
>
> **We'll cover: your core values, 5-year vision, this year's theme, how you make decisions, and what success looks like.**
>
> **This one matters A LOT - it's how Ziggy will help you prioritize everything."**

### Sections to Build

#### 1. Core Values
Ask about:
- What matters MOST to your family?
- Get 3-5 values in priority order

Example questions:
- "What are your top 3-5 values? What matters MOST to you as a family?"
- "If you had to rank them, what comes first?"

Listen for:
- Family connection
- Health
- Financial security
- Personal growth
- Home as sanctuary
- Learning
- Adventure
- Community
- [Their own values]

Push for **priority order** - "If you had to choose between X and Y, which wins?"

#### 2. 5-Year Vision
Ask about:
- Where do you want to be in 5 years?
- What does life look like?

Example questions:
- "Fast forward 5 years - what's different? What have you built?"
- "What does 2030 look like for your family?"

Push for concrete details:
- Kids' ages and what that means
- Financial goals
- Health goals
- Home situation
- Work situation

#### 3. This Year's Theme
Ask about:
- What's the focus THIS year?
- One sentence theme

Example questions:
- "If this year had a theme, what would it be?"
- "What's the ONE thing you're focusing on this year?"

Examples:
- "Building Sustainable Systems"
- "Health First"
- "Financial Reset"
- "Family Connection"

#### 4. Decision Framework
Ask about:
- How do you decide what to do?
- What makes you say yes vs. no?

Example questions:
- "When deciding whether to take something on, what do you consider?"
- "What makes something a 'yes' vs. a 'no' for you?"

Help them articulate:
- Say YES if: [aligns with values, supports vision, have capacity, simplifies life]
- Say NO if: ['should' do it, adds complexity, takes from core values, no capacity]

#### 5. Success Definition
Ask about:
- What does success actually look like?
- NOT perfection - what's GOOD ENOUGH?

Example questions:
- "What does success look like day-to-day? Week-to-week?"
- "What are you NOT trying to do? What would be over-achieving?"

Push for realistic, concrete:
- Not: "Perfect house"
- Yes: "Coming home doesn't feel overwhelming"

### Save the Pillar

```
Call ziggy_update_foundation with:
  pillar = "vision"
  content = """# Vision & Values

> **Purpose:** What matters and where you're heading.

## Core Values

**What matters most to us:**

1. **[Value 1]**
   - [What this means]

2. **[Value 2]**
   - [What this means]

3. **[Value 3]**
   - [What this means]

[etc.]

## 5-Year Vision

**By [Year], we want to have:**

**Family:**
- [Their vision]

**Health:**
- [Their vision]

**Financial:**
- [Their vision]

**Home:**
- [Their vision]

**Personal:**
- [Their vision]

## This Year's Theme

**[Year]: [Theme Name]**

[What this theme means]

**Focus areas:**
1. [Focus 1]
2. [Focus 2]
3. [Focus 3]

## Decision Framework

**When choosing what to do:**

Say yes if:
- [Their criteria]

Say no if:
- [Their criteria]

## Success Definition

**Not:**
- [What they're NOT trying to do]

**Yes:**
- [What good enough looks like]

---

**Last updated:** [Today's date]
**Review schedule:** Annually for vision, quarterly for alignment check
"""
```

---

## Wrap-Up

After all 5 pillars are saved:

> **"That's it! You've just built all 5 foundation pillars!**
>
> **Your pillars are now stored and powering Ziggy:**
> - reality (Life Reality)
> - family (Family Understanding)
> - context (Life Context)
> - capability (Household Capability)
> - vision (Vision & Values)
>
> **These pillars now power all of Ziggy's agents. Every suggestion will be grounded in YOUR reality, aligned with YOUR values, and realistic for YOUR capacity.**
>
> **Next steps:**
> 1. Try asking Ziggy to capture a task - it'll use your foundation to prioritize it intelligently
> 2. Set a reminder to update Life Context monthly (it changes most frequently)
> 3. Try your first weekly planning session
>
> **Ready to start using Ziggy?"**

---

## Important Notes

### Tone Throughout
- **Warm and encouraging**, not bureaucratic
- **Celebrate progress** after each pillar
- **Normalize imperfection** - "This doesn't need to be perfect, we can refine it"
- **Keep it conversational** - not an interrogation

### What to Capture
- **Enough to be useful**, not everything
- **Patterns, not details** - "weekday evenings are low energy" not every single hour
- **Reality, not aspiration** - what IS, not what should be

### What NOT to Capture
- **Task lists** (those live in your task manager)
- **Event schedules** (those live in your calendar)
- **Granular daily details** (that's too much)
- **Things that change weekly** (this is strategic context)

### Pillar Names for MCP Tool Calls
When calling `ziggy_update_foundation`, use these exact pillar values:
- `reality` — Life Reality
- `family` — Family Understanding
- `context` — Life Context
- `capability` — Household Capability
- `vision` — Vision & Values

---

## Troubleshooting

**If user gets overwhelmed:**
- "We can pause anytime and come back. No rush."
- "You don't need to have all the answers. Share what you know."

**If they're too vague:**
- Ask follow-up questions
- Give examples from their earlier answers
- "Tell me more about..."

**If they're over-detailing:**
- Gently redirect: "That's great - let me capture the high-level pattern here..."
- Summarize what you're hearing and confirm

**If they're aspirational (not reality):**
- "That sounds like a goal - let's come back to what's actually true RIGHT NOW"
- "I hear the 'should' - what's the reality?"

**If a `ziggy_update_foundation` call fails:**
- Let the user know: "I hit a hiccup saving that pillar. Let me try again."
- Retry the tool call with the same content
- If it continues to fail, save the content in the conversation and note it needs to be saved manually

---

## Success Criteria

Onboarding is successful when:
1. `ziggy_setup` was called with the user's name
2. All 5 pillars created and saved via `ziggy_update_foundation`
3. Each pillar has enough content to be useful (not blank or skeletal)
4. Content reflects REALITY, not aspiration
5. User understands what these are for
6. User feels good about the process (not overwhelmed or exhausted)
