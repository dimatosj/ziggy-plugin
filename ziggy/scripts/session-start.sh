#!/usr/bin/env bash
# Ziggy SessionStart hook — load user context or prompt for setup.

ZIGGY_DIR="${ZIGGY_DATA_DIR:-$HOME/.ziggy}"

if [ ! -d "$ZIGGY_DIR" ]; then
    echo "Ziggy is installed but not set up yet. Say \"set up ziggy\" to get started."
    exit 0
fi

CONFIG_FILE="$ZIGGY_DIR/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Ziggy data directory exists but config is missing. Say \"set up ziggy\" to re-initialize."
    exit 0
fi

# Read user name from config
USER_NAME=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['user_name'])" 2>/dev/null || echo "Unknown")

# Read household members
MEMBERS=$(python3 -c "import json; c=json.load(open('$CONFIG_FILE')); print(', '.join(c.get('household',{}).get('members',['$USER_NAME'])))" 2>/dev/null || echo "$USER_NAME")

# Count active tasks
TASK_FILE="$ZIGGY_DIR/tasks/tasks.json"
if [ -f "$TASK_FILE" ]; then
    TASK_STATS=$(python3 -c "
import json
tasks = json.load(open('$TASK_FILE'))
active = [t for t in tasks if t['status'] in ('inbox', 'active')]
urgent = len([t for t in active if t.get('priority') == 'URGENT'])
high = len([t for t in active if t.get('priority') == 'HIGH'])
print(f'{len(active)} ({urgent} urgent, {high} high)')
" 2>/dev/null || echo "0")
else
    TASK_STATS="0"
fi

# Check foundation
FOUNDATION_EXISTS="no"
if [ -d "$ZIGGY_DIR/foundation" ] && [ "$(ls -A "$ZIGGY_DIR/foundation" 2>/dev/null)" ]; then
    FOUNDATION_EXISTS="yes"
fi

# Check pending reviews
PENDING_REVIEWS=""
for rtype in weekly monthly quarterly; do
    if [ -f "$ZIGGY_DIR/reviews/${rtype}-state.json" ]; then
        PENDING_REVIEWS="$PENDING_REVIEWS $rtype"
    fi
done
if [ -z "$PENDING_REVIEWS" ]; then
    PENDING_REVIEWS="none"
fi

echo "--- ZIGGY CONTEXT ---"
echo "User: $USER_NAME"
echo "Household: $MEMBERS"
echo "Active tasks: $TASK_STATS"
echo "Pending reviews:$PENDING_REVIEWS"
echo "Foundation loaded: $FOUNDATION_EXISTS"
echo "--- END CONTEXT ---"
