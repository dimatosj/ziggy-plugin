"""Ziggy MCP Server — exposes task, entity, review, and foundation tools."""
import json
import os
import sys
from pathlib import Path

# Add the servers directory to Python path for ziggy package imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP

from ziggy.services.local_task_service import LocalTaskService
from ziggy.services.foundation_service import FoundationService
from ziggy.services.entity_service import EntityService
from ziggy.services.review_state_service import ReviewStateService
from ziggy.orchestrators.capture_orchestrator import CaptureOrchestrator
from ziggy.models.foundation import PillarName
from ziggy.models.config import ZiggyConfig

mcp = FastMCP("ziggy")


def get_data_dir() -> Path:
    """Get data directory from env var, defaulting to ~/.ziggy."""
    raw = os.environ.get("ZIGGY_DATA_DIR", "~/.ziggy")
    return Path(raw).expanduser()


def _load_config() -> dict:
    """Load user config if it exists."""
    config_path = get_data_dir() / "config.json"
    if config_path.exists():
        return json.loads(config_path.read_text())
    return {}


# Service singletons (initialized lazily)
_data_dir = None
_task_service = None
_foundation_service = None
_entity_service = None
_review_service = None
_orchestrator = None


class NotInitializedError(Exception):
    """Raised when Ziggy data directory is not set up."""
    pass


def _ensure_services():
    """Initialize services if not yet done. Raises NotInitializedError if ~/.ziggy/ not set up."""
    global _data_dir, _task_service, _foundation_service, _entity_service, _review_service, _orchestrator
    if _task_service is not None:
        return
    _data_dir = get_data_dir()
    if not (_data_dir / "config.json").exists():
        raise NotInitializedError()
    _task_service = LocalTaskService(_data_dir)
    _foundation_service = FoundationService(_data_dir)
    _entity_service = EntityService(_data_dir)
    _review_service = ReviewStateService(_data_dir)
    config = _load_config()
    _orchestrator = CaptureOrchestrator(config=config)


def _not_initialized_error():
    return json.dumps({"error": "Ziggy not initialized. Run ziggy_setup first.", "code": "NOT_INITIALIZED"})


# ── Setup Tool ──

@mcp.tool(name="ziggy_setup")
async def setup(user_name: str) -> str:
    """Initialize ~/.ziggy/ directory structure and config."""
    global _data_dir, _task_service, _foundation_service, _entity_service, _review_service, _orchestrator
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "foundation").mkdir(exist_ok=True)
    (data_dir / "tasks").mkdir(exist_ok=True)
    (data_dir / "entities").mkdir(exist_ok=True)
    (data_dir / "entities" / "profiles" / "people").mkdir(parents=True, exist_ok=True)
    (data_dir / "entities" / "profiles" / "organizations").mkdir(parents=True, exist_ok=True)
    (data_dir / "entities" / "profiles" / "properties").mkdir(parents=True, exist_ok=True)
    (data_dir / "reviews").mkdir(exist_ok=True)
    (data_dir / "reviews" / "history").mkdir(exist_ok=True)

    config = ZiggyConfig(user_name=user_name)
    config_path = data_dir / "config.json"
    config_path.write_text(json.dumps(config.model_dump(), indent=2))

    # Re-initialize services with new data dir
    _data_dir = data_dir
    _task_service = LocalTaskService(data_dir)
    _foundation_service = FoundationService(data_dir)
    _entity_service = EntityService(data_dir)
    _review_service = ReviewStateService(data_dir)
    _orchestrator = CaptureOrchestrator(config=config.model_dump())

    return json.dumps({"status": "initialized", "data_dir": str(data_dir)})


# ── Capture / Task Tools ──

@mcp.tool(name="ziggy_analyze")
async def analyze(text: str) -> str:
    """Analyze text: classify entity type, score priority, detect domain, detect entity mentions. Pure analysis — does NOT store anything."""
    try:
        _ensure_services()
    except NotInitializedError:
        return _not_initialized_error()
    result = _orchestrator.analyze(text)
    return json.dumps(result, default=str)


@mcp.tool(name="ziggy_store_task")
async def store_task(title: str, analysis: str, description: str = "", due_date: str = "") -> str:
    """Store an analyzed item as a task with inbox status."""
    try:
        _ensure_services()
    except NotInitializedError:
        return _not_initialized_error()
    analysis_dict = json.loads(analysis) if isinstance(analysis, str) else analysis
    task = _task_service.store_task(
        title=title,
        analysis=analysis_dict,
        description=description,
        due_date=due_date or None,
    )
    return json.dumps(task.model_dump(), default=str)


@mcp.tool(name="ziggy_store_draft")
async def store_draft(title: str, type: str, analysis: str, description: str = "") -> str:
    """Store an analyzed item as a draft (project/goal/commitment/initiative)."""
    try:
        _ensure_services()
    except NotInitializedError:
        return _not_initialized_error()
    analysis_dict = json.loads(analysis) if isinstance(analysis, str) else analysis
    draft = _task_service.store_draft(
        title=title,
        type=type,
        analysis=analysis_dict,
        description=description,
    )
    return json.dumps(draft.model_dump(), default=str)


@mcp.tool(name="ziggy_list_tasks")
async def list_tasks(status: str = "", domain: str = "", priority: str = "") -> str:
    """List tasks with optional filters."""
    try:
        _ensure_services()
    except NotInitializedError:
        return _not_initialized_error()
    tasks = _task_service.list_tasks(
        status=status or None,
        domain=domain or None,
        priority=priority or None,
    )
    return json.dumps([t.model_dump() for t in tasks], default=str)


@mcp.tool(name="ziggy_update_task")
async def update_task(id: str, status: str = "", priority: str = "", title: str = "") -> str:
    """Update task fields."""
    try:
        _ensure_services()
    except NotInitializedError:
        return _not_initialized_error()
    kwargs = {}
    if status:
        kwargs["status"] = status
    if priority:
        kwargs["priority"] = priority
    if title:
        kwargs["title"] = title
    try:
        task = _task_service.update_task(id, **kwargs)
        return json.dumps(task.model_dump(), default=str)
    except KeyError:
        return json.dumps({"error": f"Task not found: {id}", "code": "NOT_FOUND"})


@mcp.tool(name="ziggy_list_drafts")
async def list_drafts(type: str = "") -> str:
    """List drafts with optional type filter."""
    try:
        _ensure_services()
    except NotInitializedError:
        return _not_initialized_error()
    drafts = _task_service.list_drafts(type=type or None)
    return json.dumps([d.model_dump() for d in drafts], default=str)


@mcp.tool(name="ziggy_update_draft")
async def update_draft(id: str, status: str = "", title: str = "", type: str = "") -> str:
    """Update draft fields or delete a draft (status='deleted')."""
    try:
        _ensure_services()
    except NotInitializedError:
        return _not_initialized_error()
    if status == "deleted":
        try:
            _task_service.delete_draft(id)
            return json.dumps({"status": "deleted", "id": id})
        except KeyError:
            return json.dumps({"error": f"Draft not found: {id}", "code": "NOT_FOUND"})
    kwargs = {}
    if status:
        kwargs["status"] = status
    if title:
        kwargs["title"] = title
    if type:
        kwargs["type"] = type
    try:
        draft = _task_service.update_draft(id, **kwargs)
        return json.dumps(draft.model_dump(), default=str)
    except KeyError:
        return json.dumps({"error": f"Draft not found: {id}", "code": "NOT_FOUND"})


# ── Entity Tools ──

@mcp.tool(name="ziggy_resolve_entity")
async def resolve_entity(query: str) -> str:
    """Find entity by name (exact, fuzzy, ambiguous, unknown)."""
    try:
        _ensure_services()
    except NotInitializedError:
        return _not_initialized_error()
    result = _entity_service.resolve(query)
    return json.dumps(result, default=str)


@mcp.tool(name="ziggy_create_entity")
async def create_entity(
    name: str,
    type: str,
    subtype: str = "",
    domain: str = "",
    description: str = "",
    aliases: str = "",
    contact_email: str = "",
    contact_phone: str = "",
) -> str:
    """Create a new entity with optional profile."""
    try:
        _ensure_services()
    except NotInitializedError:
        return _not_initialized_error()
    alias_list = [a.strip() for a in aliases.split(",") if a.strip()] if aliases else []
    contact_info = {}
    if contact_email:
        contact_info["email"] = contact_email
    if contact_phone:
        contact_info["phone"] = contact_phone
    entity = _entity_service.create_entity(
        name=name,
        entity_type=type,
        subtype=subtype,
        domain=domain,
        description=description,
        aliases=alias_list,
        contact_info=contact_info,
    )
    return json.dumps(entity, default=str)


@mcp.tool(name="ziggy_list_entities")
async def list_entities(type: str = "", domain: str = "") -> str:
    """Browse entities with optional filters."""
    try:
        _ensure_services()
    except NotInitializedError:
        return _not_initialized_error()
    entities = _entity_service.get_all()
    if type:
        entities = [e for e in entities if e.get("type") == type]
    if domain:
        entities = [e for e in entities if e.get("domain") == domain]
    return json.dumps(entities, default=str)


@mcp.tool(name="ziggy_detect_mentions")
async def detect_mentions(text: str) -> str:
    """Find entity mentions in text."""
    try:
        _ensure_services()
    except NotInitializedError:
        return _not_initialized_error()
    mentions = _orchestrator.entity_detector.detect_mentions(text)
    return json.dumps(mentions, default=str)


# ── Review Tools ──

@mcp.tool(name="ziggy_get_review_state")
async def get_review_state(type: str) -> str:
    """Load review state (weekly/monthly/quarterly)."""
    try:
        _ensure_services()
    except NotInitializedError:
        return _not_initialized_error()
    try:
        state = _review_service.get_state(type)
        if state is None:
            return json.dumps({"status": "no_active_review", "type": type})
        return json.dumps(state, default=str)
    except ValueError as e:
        return json.dumps({"error": str(e), "code": "INVALID_INPUT"})


@mcp.tool(name="ziggy_save_review_state")
async def save_review_state(type: str, state: str) -> str:
    """Persist review progress."""
    try:
        _ensure_services()
    except NotInitializedError:
        return _not_initialized_error()
    state_dict = json.loads(state) if isinstance(state, str) else state
    try:
        _review_service.save_state(type, state_dict)
        return json.dumps({"status": "saved", "type": type})
    except ValueError as e:
        return json.dumps({"error": str(e), "code": "INVALID_INPUT"})


@mcp.tool(name="ziggy_clear_review_state")
async def clear_review_state(type: str) -> str:
    """Clear completed review."""
    try:
        _ensure_services()
    except NotInitializedError:
        return _not_initialized_error()
    try:
        _review_service.clear_state(type)
        return json.dumps({"status": "cleared", "type": type})
    except ValueError as e:
        return json.dumps({"error": str(e), "code": "INVALID_INPUT"})


# ── Foundation Tools ──

@mcp.tool(name="ziggy_get_foundation")
async def get_foundation() -> str:
    """Read all foundation pillars."""
    try:
        _ensure_services()
    except NotInitializedError:
        return _not_initialized_error()
    pillars = _foundation_service.read_all()
    return json.dumps(pillars, default=str)


@mcp.tool(name="ziggy_update_foundation")
async def update_foundation(pillar: str, content: str) -> str:
    """Update a foundation pillar."""
    try:
        _ensure_services()
    except NotInitializedError:
        return _not_initialized_error()
    try:
        pillar_enum = PillarName(pillar)
    except ValueError:
        return json.dumps({
            "error": f"Invalid pillar: {pillar}. Must be one of: {[p.value for p in PillarName]}",
            "code": "INVALID_INPUT",
        })
    _foundation_service.write_pillar(pillar_enum, content)
    return json.dumps({"status": "updated", "pillar": pillar})


@mcp.tool(name="ziggy_get_config")
async def get_config() -> str:
    """Read user configuration."""
    try:
        _ensure_services()
    except NotInitializedError:
        return _not_initialized_error()
    config = _load_config()
    if not config:
        return _not_initialized_error()
    return json.dumps(config, default=str)


if __name__ == "__main__":
    mcp.run()
