from pathlib import Path
import json
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

# Load configuration
ROOT = Path(__file__).parent
THRESHOLDS = json.loads((ROOT / "thresholds.json").read_text(encoding="utf-8"))

# Simple rule evaluator that replaces json_logic
def evaluate_rules(rules, data):
    """Evaluate rules without using json_logic library."""
    if isinstance(rules, dict):
        # Handle logical operators
        if "and" in rules:
            return all(evaluate_rules(condition, data) for condition in rules["and"])
        elif "or" in rules:
            return any(evaluate_rules(condition, data) for condition in rules["or"])
        elif "not" in rules:
            return not evaluate_rules(rules["not"], data)
        
        # Handle comparison operators
        elif "<" in rules:
            return evaluate_comparison(rules["<"], data, lambda a, b: a < b)
        elif "<=" in rules:
            return evaluate_comparison(rules["<="], data, lambda a, b: a <= b)
        elif ">" in rules:
            return evaluate_comparison(rules[">"], data, lambda a, b: a > b)
        elif ">=" in rules:
            return evaluate_comparison(rules[">="], data, lambda a, b: a >= b)
        elif "==" in rules:
            return evaluate_comparison(rules["=="], data, lambda a, b: a == b)
        elif "!=" in rules:
            return evaluate_comparison(rules["!="], data, lambda a, b: a != b)
        
        # Handle variable reference
        elif "var" in rules:
            var_path = rules["var"].split(".")
            value = data
            for key in var_path:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return None
            return value
        
        # Handle if-then-else
        elif "if" in rules:
            conditions = rules["if"]
            if len(conditions) >= 3:
                # Format: [condition, then_value, else_value]
                if evaluate_rules(conditions[0], data):
                    return evaluate_rules(conditions[1], data)
                else:
                    return evaluate_rules(conditions[2], data)
    
    # Return literal values
    return rules

def evaluate_comparison(operands, data, operator_func):
    """Helper function to evaluate comparison operators."""
    if len(operands) != 2:
        return False
    
    left = evaluate_rules(operands[0], data)
    right = evaluate_rules(operands[1], data)
    
    try:
        return operator_func(left, right)
    except:
        return False

# Load rules from thresholds.json or define them here
try:
    RULES = THRESHOLDS.get("rules", {
        "and": [
            {"<": [{"var": "claimant_age"}, THRESHOLDS.get("max_age", 70)]},
            {"<": [{"var": "num_children"}, THRESHOLDS.get("max_children", 5)]},
            {"<": [{"var": "monthly_income"}, THRESHOLDS.get("max_income", 100000)]}
        ]
    })
except:
    # Fallback rules if thresholds.json doesn't have rules
    RULES = {
        "and": [
            {"<": [{"var": "claimant_age"}, 70]},
            {"<": [{"var": "num_children"}, 5]},
            {"<": [{"var": "monthly_income"}, 100000]}
        ]
    }

# Pydantic model for input
class ChildAllowanceInput(BaseModel):
    """Schema for checking Serbian child allowance eligibility."""
    claimant_age: int = Field(description="Age of the claimant in years")
    num_children: int = Field(description="Number of children in the household")
    monthly_income: float = Field(description="Total monthly household income in RSD")

def check_child_allowance(
    claimant_age: int,
    num_children: int,
    monthly_income: float
) -> str:
    """
    Determine eligibility for Serbian child allowance based on the provided criteria.
    Returns a string explanation of eligibility in Serbian.
    """
    payload = {
        "claimant_age": claimant_age,
        "num_children": num_children,
        "monthly_income": monthly_income
    }
    
    try:
        # Use our custom rule evaluator instead of jsonLogic
        is_eligible = evaluate_rules(RULES, payload)
        
        if is_eligible:
            return (
                f"✅ IMATE PRAVO na dečiji dodatak!\n\n"
                f"Vaši podaci:\n"
                f"- Starost: {claimant_age} godina\n"
                f"- Broj dece: {num_children}\n"
                f"- Mesečni prihod: {monthly_income:,.0f} RSD\n\n"
                f"Svi uslovi su ispunjeni."
            )
        else:
            # Build detailed reason for ineligibility
            reasons = []
            max_age = THRESHOLDS.get("max_age", 70)
            max_children = THRESHOLDS.get("max_children", 5) - 1  # Subtract 1 because rule is <5 not <=4
            max_income = THRESHOLDS.get("max_income", 100000)
            
            if claimant_age >= max_age:
                reasons.append(f"- Vaša starost ({claimant_age}) prelazi limit od {max_age} godina")
            if num_children > max_children:
                reasons.append(f"- Broj dece ({num_children}) prelazi limit od {max_children}")
            if monthly_income >= max_income:
                reasons.append(f"- Mesečni prihod ({monthly_income:,.0f} RSD) prelazi limit od {max_income:,.0f} RSD")
            
            return (
                f"❌ NEMATE PRAVO na dečiji dodatak.\n\n"
                f"Razlozi:\n" + "\n".join(reasons) if reasons else "Uslovi nisu ispunjeni."
            )
            
    except Exception as e:
        return f"Greška pri proveri: {str(e)}. Molimo pokušajte ponovo sa validnim podacima."

# Create the structured tool
eligibility_tool = StructuredTool.from_function(
    func=check_child_allowance,
    name="check_child_allowance",
    description="Check eligibility for Serbian child allowance based on age, number of children, and income",
    args_schema=ChildAllowanceInput,
    return_direct=False
)
