"""
templates.py – defines predefined legal workflow templates.
"""
from __future__ import annotations

from typing import Any, Dict

WORKFLOW_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "contract_review": {
        "name": "Contract Risk & Mitigation Report",
        "description": "Upload a contract, extract key clauses, identify legal risks, and compile suggestions.",
        "steps": [
            {
                "id": "extract_clauses",
                "name": "Extract Clauses",
                "input_keys": ["contract_text"],
                "output_keys": ["extracted_clauses"]
            },
            {
                "id": "review_clauses",
                "name": "Review Clauses",
                "input_keys": ["extracted_clauses"],
                "output_keys": ["clause_reviews"]
            },
            {
                "id": "find_risks",
                "name": "Find Risks",
                "input_keys": ["clause_reviews"],
                "output_keys": ["identified_risks"]
            },
            {
                "id": "draft_suggestions",
                "name": "Draft Suggestions",
                "input_keys": ["identified_risks"],
                "output_keys": ["mitigation_suggestions"]
            },
            {
                "id": "generate_report",
                "name": "Generate Report",
                "input_keys": ["extracted_clauses", "identified_risks", "mitigation_suggestions"],
                "output_keys": ["final_report"]
            }
        ]
    }
}
