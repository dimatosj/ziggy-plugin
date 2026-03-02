# Ziggy — Personal Life OS Plugin for Claude Code

Ziggy is a personal life operating system that runs as a Claude Code plugin. It provides task capture and management, entity intelligence (people, places, organizations), structured life reviews (weekly, monthly, quarterly), and a foundation system for tracking your values, reality, and vision. All data stays local on your machine in `~/.ziggy/`.

## Prerequisites

- **Claude Code** (latest version with plugin support)
- **Python 3.11+** (`python3 --version`)
- **pip packages**: `mcp>=1.0`, `pydantic>=2.0`

## Installation

1. Install Python dependencies:

```bash
pip install -r servers/requirements.txt
```

2. Load the plugin in Claude Code:

```bash
# Development / one-off
claude --plugin-dir /path/to/ziggy-plugin

# Or add to your Claude Code settings for permanent use
```

3. On first run, Ziggy will detect it hasn't been set up and guide you through the **onboard** flow to initialize `~/.ziggy/` and build your foundation pillars.

## Available Skills

| Skill | Trigger | Description |
|-------|---------|-------------|
| **onboard** | "get started", "set up ziggy" | Initialize Ziggy and build your 5 foundation pillars (Reality, Family, Context, Capability, Vision) |
| **capture** | "brain dump", messy task list | Analyze and store tasks with priority scoring, domain detection, and entity awareness |
| **entity-lookup** | "who is X?", "what do I know about X?" | Look up people, places, and organizations — or create new ones |
| **daily-start** | "start my day", "what's on today?" | Morning briefing with task summary, urgent items, and pending reviews |
| **weekly-review** | "weekly review" | Tactical review: incomplete tasks, triage, draft review, domain balance |
| **monthly-review** | "monthly review" | Weekly review + commitment check-ins, expanded draft review, capacity assessment |
| **quarterly-review** | "quarterly review" | Strategic review: quarter reflection, foundation update, next quarter planning |

## Data Location

All Ziggy data is stored in `~/.ziggy/` (configurable via `ZIGGY_DATA_DIR` environment variable):

```
~/.ziggy/
├── config.json          # User configuration
├── foundation/          # Foundation pillar markdown files
│   ├── reality.md
│   ├── family.md
│   ├── context.md
│   ├── capability.md
│   └── vision.md
├── tasks/
│   ├── tasks.json       # Active tasks
│   └── drafts.json      # Draft items (projects, goals, etc.)
├── entities/
│   ├── index.json       # Entity lookup index
│   └── profiles/        # Rich entity profiles
│       ├── people/
│       ├── organizations/
│       └── properties/
└── reviews/
    ├── weekly-state.json
    ├── monthly-state.json
    └── quarterly-state.json
```

## How It Works

Ziggy uses a four-layer architecture:

1. **Skills** (`skills/`) — Markdown workflow guides that Claude follows step-by-step. They encode the intelligence: what questions to ask, how to interpret answers, when to use which tools.

2. **Hooks** (`hooks/`) — Automatic actions triggered by Claude Code events. The `SessionStart` hook loads your context (user name, task counts, foundation status) at the beginning of each conversation.

3. **MCP Server** (`servers/ziggy_server.py`) — A FastMCP Python server exposing 17 tools for task management, entity operations, review state, and foundation editing. Claude calls these tools as directed by the skills.

4. **Local Storage** (`~/.ziggy/`) — All data persists as JSON files and markdown on your local filesystem. No cloud services, no API keys required.

## MCP Tools Reference

| Tool | Description |
|------|-------------|
| `ziggy_setup` | Initialize ~/.ziggy/ directory and config |
| `ziggy_analyze` | Analyze text for entity type, priority, domain |
| `ziggy_store_task` | Store an analyzed item as a task |
| `ziggy_store_draft` | Store an item as a draft (project/goal/etc.) |
| `ziggy_list_tasks` | List tasks with optional filters |
| `ziggy_update_task` | Update task fields (status, priority, title) |
| `ziggy_list_drafts` | List drafts with optional type filter |
| `ziggy_resolve_entity` | Find entity by name (exact, fuzzy, ambiguous) |
| `ziggy_create_entity` | Create a new entity with profile |
| `ziggy_list_entities` | Browse entities with optional filters |
| `ziggy_detect_mentions` | Find entity mentions in text |
| `ziggy_get_review_state` | Load review progress (weekly/monthly/quarterly) |
| `ziggy_save_review_state` | Persist review progress |
| `ziggy_clear_review_state` | Clear completed review |
| `ziggy_get_foundation` | Read all foundation pillars |
| `ziggy_update_foundation` | Update a foundation pillar |
| `ziggy_get_config` | Read user configuration |

## Running Tests

```bash
cd ziggy-plugin
PYTHONPATH=servers python3 -m pytest tests/ -v
```

## License

MIT
