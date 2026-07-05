"""
router.py – exposes FastAPI endpoints for creating, running, and monitoring legal workflows.
"""
from __future__ import annotations

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel

from .state import WorkflowInstance
from .templates import WORKFLOW_TEMPLATES
from .scheduler import WorkflowScheduler

router = APIRouter(prefix="/workflows", tags=["Workflow Engine"])
scheduler = WorkflowScheduler()

# ── Request Models ────────────────────────────────────────────────────────
class WorkflowStartRequest(BaseModel):
    template_name: str
    inputs: Dict[str, Any]

# ── Endpoints ─────────────────────────────────────────────────────────────
@router.post(
    "/start",
    response_model=WorkflowInstance,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new legal workflow run"
)
async def start_workflow(
    request: WorkflowStartRequest,
    background_tasks: BackgroundTasks
) -> WorkflowInstance:
    """
    Spins up a new workflow run based on the specified template.
    Runs the stages asynchronously in a background thread.
    """
    try:
        instance = scheduler.create_workflow(request.template_name, request.inputs)
        # Use scheduler's background execution
        scheduler.run_workflow_async(instance.workflow_id)
        return instance
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc)
        )

@router.get(
    "/templates/list",
    summary="List all available legal workflow templates"
)
async def list_templates() -> Dict[str, Any]:
    """
    Returns metadata of all configured workflow templates.
    """
    return {
        name: {
            "name": cfg["name"],
            "description": cfg["description"],
            "step_count": len(cfg["steps"])
        }
        for name, cfg in WORKFLOW_TEMPLATES.items()
    }

@router.get(
    "/{workflow_id}",
    response_model=WorkflowInstance,
    summary="Get the execution status of a workflow run"
)
async def get_workflow_status(workflow_id: str) -> WorkflowInstance:
    """
    Polls the current execution state, steps status, context, and outputs.
    """
    instance = scheduler.get_workflow(workflow_id)
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow run '{workflow_id}' not found."
        )
    return instance
