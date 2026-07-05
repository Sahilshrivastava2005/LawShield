"""
scheduler.py – schedules, runs, and monitors legal workflow instances.
"""
from __future__ import annotations

import logging
import threading
import uuid
from typing import Dict, Any, Optional

from .state import WorkflowInstance, WorkflowStep
from .templates import WORKFLOW_TEMPLATES
from .executor import WorkflowExecutor

logger = logging.getLogger(__name__)

# Thread-safe in-memory database of active workflow runs
_active_workflows: Dict[str, WorkflowInstance] = {}
_workflows_lock = threading.Lock()

class WorkflowScheduler:
    """
    Schedules and runs workflows in the background.
    """

    def __init__(self, provider_name: str | None = None) -> None:
        self.executor = WorkflowExecutor(provider_name)

    def create_workflow(self, template_name: str, inputs: Dict[str, Any]) -> WorkflowInstance:
        """
        Creates a new workflow instance from a template and registers it in memory.
        """
        if template_name not in WORKFLOW_TEMPLATES:
            raise ValueError(f"Template '{template_name}' does not exist.")

        config = WORKFLOW_TEMPLATES[template_name]
        workflow_id = str(uuid.uuid4())

        steps = []
        for step_cfg in config["steps"]:
            steps.append(WorkflowStep(
                id=step_cfg["id"],
                name=step_cfg["name"],
                input_keys=step_cfg["input_keys"],
                output_keys=step_cfg["output_keys"]
            ))

        instance = WorkflowInstance(
            workflow_id=workflow_id,
            template_name=template_name,
            steps=steps,
            global_context=inputs
        )

        with _workflows_lock:
            _active_workflows[workflow_id] = instance

        logger.info("Created workflow instance %s (template: %s)", workflow_id, template_name)
        return instance

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowInstance]:
        """
        Retrieves a workflow run from memory.
        """
        with _workflows_lock:
            return _active_workflows.get(workflow_id)

    def run_workflow_sync(self, workflow_id: str) -> None:
        """
        Executes a workflow synchronously step-by-step.
        """
        instance = self.get_workflow(workflow_id)
        if not instance:
            logger.error("Workflow run %s not found.", workflow_id)
            return

        instance.status = "running"
        logger.info("Starting execution of workflow %s", workflow_id)

        for i, step in enumerate(instance.steps):
            instance.current_step_index = i
            
            # Execute step
            self.executor.execute_step(instance, step)
            
            if step.status == "failed":
                instance.status = "failed"
                logger.error("Workflow %s aborted due to failure at step '%s'.", workflow_id, step.id)
                return

        instance.status = "completed"
        logger.info("Workflow %s completed successfully.", workflow_id)

    def run_workflow_async(self, workflow_id: str) -> None:
        """
        Spins off a background thread to execute the workflow.
        """
        thread = threading.Thread(target=self.run_workflow_sync, args=(workflow_id,))
        thread.daemon = True
        thread.start()
        logger.info("Workflow %s execution dispatched to background thread.", workflow_id)
