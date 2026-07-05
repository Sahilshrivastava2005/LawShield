"""
executor.py – executes steps of a workflow instance using LLM capabilities.
"""
from __future__ import annotations

import logging
from typing import Dict, Any

from langchain_core.messages import HumanMessage, SystemMessage
from llm.providers.factory import get_llm_provider
from .state import WorkflowInstance, WorkflowStep

logger = logging.getLogger(__name__)

class WorkflowExecutor:
    """
    Executes individual steps of a running legal workflow.
    """

    def __init__(self, provider_name: str | None = None) -> None:
        self.provider_name = provider_name
        self.model = get_llm_provider(provider_name).get_model()

    def execute_step(self, instance: WorkflowInstance, step: WorkflowStep) -> None:
        """
        Executes the logic for the given step using context variables,
        updates the step outputs, and saves them to the instance global_context.
        """
        logger.info("Executing step '%s' (%s) for workflow %s", step.id, step.name, instance.workflow_id)
        step.status = "running"
        instance.touch()

        # Gather inputs from the global context
        inputs = {}
        for key in step.input_keys:
            if key in instance.global_context:
                inputs[key] = instance.global_context[key]
            else:
                step.status = "failed"
                step.error = f"Missing required input key: '{key}'"
                logger.error("Step '%s' failed: %s", step.id, step.error)
                return

        try:
            # Route based on step ID
            outputs = self._run_step_logic(step.id, inputs)
            
            # Update step and global context
            step.outputs = outputs
            step.status = "completed"
            for out_key in step.output_keys:
                if out_key in outputs:
                    instance.global_context[out_key] = outputs[out_key]
                else:
                    logger.warning("Step logic did not return expected output key: %s", out_key)

        except Exception as exc:
            step.status = "failed"
            step.error = str(exc)
            logger.error("Execution failed for step '%s': %s", step.id, step.error)

        instance.touch()

    def _run_step_logic(self, step_id: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invokes LLM prompts based on step ID.
        """
        if step_id == "extract_clauses":
            contract = inputs.get("contract_text", "")
            prompt = (
                "Extract the main legal clauses (such as Limitation of Liability, Indemnity, "
                "Governing Law, and Termination) from the following contract text. "
                "Provide a bulleted list with clause names and brief verbatim text snippets."
            )
            res = self._call_llm(prompt, contract)
            return {"extracted_clauses": res}

        elif step_id == "review_clauses":
            clauses = inputs.get("extracted_clauses", "")
            prompt = (
                "Review the following extracted contract clauses. Assess whether they favor "
                "one party over the other, or deviate from standard corporate legal standards."
            )
            res = self._call_llm(prompt, clauses)
            return {"clause_reviews": res}

        elif step_id == "find_risks":
            reviews = inputs.get("clause_reviews", "")
            prompt = (
                "Based on the clause reviews below, identify all potential legal, financial, "
                "and operational risks. Group them by severity (High, Medium, Low)."
            )
            res = self._call_llm(prompt, reviews)
            return {"identified_risks": res}

        elif step_id == "draft_suggestions":
            risks = inputs.get("identified_risks", "")
            prompt = (
                "Draft clear mitigation suggestions, redlines, or alternative clauses to address "
                "the legal risks identified below."
            )
            res = self._call_llm(prompt, risks)
            return {"mitigation_suggestions": res}

        elif step_id == "generate_report":
            clauses = inputs.get("extracted_clauses", "")
            risks = inputs.get("identified_risks", "")
            suggestions = inputs.get("mitigation_suggestions", "")
            
            prompt = (
                "Generate a consolidated, high-level Legal Risk & Mitigation Report using the "
                "following information. Use professional legal formatting in markdown."
            )
            context = (
                f"--- EXTRACTED CLAUSES ---\n{clauses}\n\n"
                f"--- IDENTIFIED RISKS ---\n{risks}\n\n"
                f"--- SUGGESTIONS ---\n{suggestions}\n"
            )
            res = self._call_llm(prompt, context)
            return {"final_report": res}

        else:
            raise ValueError(f"Unknown step ID: '{step_id}'")

    def _call_llm(self, system_instruction: str, user_content: str) -> str:
        messages = [
            SystemMessage(content=system_instruction),
            HumanMessage(content=user_content)
        ]
        return self.model.invoke(messages).content
