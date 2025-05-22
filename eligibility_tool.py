# eligibility_tool.py  ── deterministic checker + LangChain tool
from __future__ import annotations
from pathlib import Path
import json
from typing import Literal, List, Dict, Any

from pydantic import BaseModel, Field, field_validator   # v2 API
from json_logic import jsonLogic                     # pip install json-logic
from langchain.tools import StructuredTool

# ---- load rule tree & thresholds once --------------------------------------
ROOT          = Path(__file__).parent
RULES         = json.loads((ROOT / "rules.json").read_text(encoding="utf-8"))["dečiji_dodatak"]
THRESHOLDS    = json.loads((ROOT / "thresholds.json").read_text(encoding="utf-8"))

# ---- schema the LLM must satisfy ------------------------------------------
class EligibilityInput(BaseModel):
    members: int = Field(..., ge=1)
    last3_net_incomes: List[float] = Field(..., min_items=3, max_items=3)
    category: Literal["regular", "single_30", "single_20"]
    liquid_assets: float = Field(..., ge=0)
    owns_extra_property: bool
    child_lives_in_rs: bool
    child_attends_school_rs: bool
    child_vaccinated: bool
    child_age: int = Field(..., ge=0)
    citizenship_ok: bool
    residence_ok: bool
    avg_salary_rs: float = Field(..., ge=0)
    
    # v2 single-field validator
    @field_validator("last3_net_incomes")
    @classmethod				# ← required in v2
    def _exactly_three(cls, v: list):   # type: ignore[override]
    	if len(v) != 3:
    	    raise ValueError("Need exactly three monthly income values")
        return v

# ---- wrapper that builds payload & runs JsonLogic -------------------------
def _run_tool(**kwargs) -> Dict[str, Any]:
    args = EligibilityInput(**kwargs)

    per_capita_income = sum(args.last3_net_incomes) / 3
    payload = {
        # raw fields
        "citizenship_ok":        args.citizenship_ok,
        "residence_ok":          args.residence_ok,
        "child_lives_in_rs":     args.child_lives_in_rs,
        "child_attends_school_rs": args.child_attends_school_rs,
        "child_vaccinated":      args.child_vaccinated,
        "child_age":             args.child_age,
        "members":               args.members,
        "liquid_assets":         args.liquid_assets,
        "owns_extra_property":   args.owns_extra_property,
        # derived + thresholds
        "avg_income_3m":             per_capita_income,
        "cenzus_current":            THRESHOLDS["cenzus"][args.category],
        "liquid_asset_multiplier":   THRESHOLDS["liquid_asset_multiplier"],
        "avg_salary_rs":             args.avg_salary_rs,
    }

    ok = jsonLogic(RULES, payload)
    return {
        "eligible": ok,
        "explanation": (
            "All statutory conditions fulfilled."
            if ok else
            "At least one statutory condition failed."
        )
    }

# ---- make the LangChain StructuredTool object -----------------------------
eligibility_tool = StructuredTool.from_function(
    name="check_child_allowance",
    description="Return eligibility for Serbian child allowance as {eligible:bool, explanation:str}",
    func=_run_tool,
    args_schema=EligibilityInput,
)
