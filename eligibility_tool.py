from pathlib import Path
import json
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from typing import Optional, Literal

# Load configuration
ROOT = Path(__file__).parent
THRESHOLDS = json.loads((ROOT / "thresholds.json").read_text(encoding="utf-8"))

# Pydantic model for comprehensive input
class ChildAllowanceInput(BaseModel):
    """Schema for checking Serbian child allowance eligibility."""
    # Basic information
    claimant_age: int = Field(description="Age of the claimant in years")
    num_children: int = Field(description="Number of children in the household")
    monthly_income: float = Field(description="Total monthly household income in RSD after taxes")
    
    # Citizenship and residence
    citizenship: Literal["serbian", "foreign_permanent", "foreign_other"] = Field(
        description="Citizenship status: 'serbian' for Serbian citizen, 'foreign_permanent' for foreign citizen with permanent residence, 'foreign_other' for other"
    )
    residence_in_serbia: bool = Field(description="Does the claimant have residence in Serbia?")
    
    # Property ownership
    owns_property: bool = Field(description="Does the family own any property besides their primary residence?")
    living_space_rooms: Optional[int] = Field(description="Number of rooms in primary residence", default=None)
    owns_agricultural_land: bool = Field(description="Does the family own agricultural land?")
    agricultural_land_hectares: Optional[float] = Field(description="Size of agricultural land in hectares", default=0)
    liquid_assets_per_member: Optional[float] = Field(description="Liquid assets (cash, stocks, etc.) per family member in RSD", default=0)
    
    # Child-specific information
    children_live_in_serbia: bool = Field(description="Do all children live in Serbia?")
    children_attend_school: bool = Field(description="Do all school-age children attend school regularly?")
    children_vaccinated: bool = Field(description="Are all children vaccinated according to Serbian regulations?")
    
    # Family status
    single_parent: bool = Field(description="Is this a single-parent family?")
    has_disabled_child: bool = Field(description="Is there a child with disabilities in the family?")
    
    # Care arrangements
    children_in_social_care: bool = Field(description="Are any children placed in social care institutions?")
    parent_has_parental_rights: bool = Field(description="Does the parent have full parental rights?")

def check_child_allowance(
    claimant_age: int,
    num_children: int,
    monthly_income: float,
    citizenship: str,
    residence_in_serbia: bool,
    owns_property: bool,
    living_space_rooms: Optional[int],
    owns_agricultural_land: bool,
    agricultural_land_hectares: float,
    liquid_assets_per_member: float,
    children_live_in_serbia: bool,
    children_attend_school: bool,
    children_vaccinated: bool,
    single_parent: bool,
    has_disabled_child: bool,
    children_in_social_care: bool,
    parent_has_parental_rights: bool
) -> str:
    """
    Comprehensive check for Serbian child allowance eligibility.
    Returns a detailed explanation in Serbian.
    """
    
    # Get thresholds from JSON
    max_age = THRESHOLDS.get("max_age", 70)
    max_children = THRESHOLDS.get("max_children", 4)
    base_income_threshold = THRESHOLDS.get("max_income", 100000)
    avg_salary = THRESHOLDS.get("average_salary", 80000)
    
    # Get multipliers from JSON
    income_multipliers = THRESHOLDS.get("income_multipliers", {})
    single_parent_multiplier = income_multipliers.get("single_parent_categories_1_5", 1.3)
    disabled_child_multiplier = income_multipliers.get("disabled_child", 1.2)
    
    # Get property limits from JSON
    property_limits = THRESHOLDS.get("property_limits", {})
    max_agricultural_per_member = property_limits.get("max_agricultural_land_per_member_hectares", 2)
    max_other_property_sqm = property_limits.get("max_other_property_sqm", 20)
    
    # Get liquid asset limits from JSON
    liquid_assets_config = THRESHOLDS.get("liquid_assets", {})
    max_liquid_multiplier = liquid_assets_config.get("max_per_member_in_average_salaries", 2)
    
    # Get cadastral income limits from JSON
    cadastral_config = THRESHOLDS.get("cadastral_income", {})
    
    # Track eligibility and reasons
    eligible = True
    ineligible_reasons = []
    warnings = []
    
    # 1. Check citizenship and residence (Article 26)
    # Handle various citizenship inputs more flexibly
    citizenship_lower = citizenship.lower()
    if citizenship_lower not in ["serbian", "srbija", "srpski", "foreign_permanent", "stalni_boravak", "permanent"]:
        eligible = False
        ineligible_reasons.append("❌ Morate biti državljanin Srbije ili imati stalni boravak")
    elif not residence_in_serbia:
        eligible = False
        ineligible_reasons.append("❌ Morate imati prebivalište u Srbiji")
    
    # 2. Check basic thresholds
    if claimant_age >= max_age:
        eligible = False
        ineligible_reasons.append(f"❌ Vaša starost ({claimant_age}) prelazi limit od {max_age} godina")
    
    if num_children > max_children:
        eligible = False
        ineligible_reasons.append(f"❌ Broj dece ({num_children}) prelazi limit od {max_children}")
    
    # 3. Adjust income threshold based on family status (using multipliers from JSON)
    income_threshold = base_income_threshold
    applied_multiplier = 1.0
    
    if single_parent:
        income_threshold *= single_parent_multiplier
        applied_multiplier = single_parent_multiplier
    elif has_disabled_child:
        income_threshold *= disabled_child_multiplier
        applied_multiplier = disabled_child_multiplier
    
    if monthly_income >= income_threshold:
        eligible = False
        ineligible_reasons.append(f"❌ Mesečni prihod ({monthly_income:,.0f} RSD) prelazi limit od {income_threshold:,.0f} RSD")
    
    # 4. Check property ownership (Articles 7-8)
    family_size = num_children + 2  # Assuming 2 parents (adjust for single parent)
    if single_parent:
        family_size = num_children + 1
    
    # Calculate max rooms dynamically from formula in JSON
    max_rooms_formula = property_limits.get("max_rooms_formula", "family_members + 1")
    max_rooms = family_size + 1  # Default implementation of the formula
    
    if owns_property:
        eligible = False
        ineligible_reasons.append("❌ Porodica ne sme posedovati dodatne nekretnine osim stambenog prostora")
    
    # Handle optional living_space_rooms
    if living_space_rooms is not None and living_space_rooms > max_rooms:
        eligible = False
        ineligible_reasons.append(f"❌ Stambeni prostor ({living_space_rooms} soba) prelazi limit od {max_rooms} soba za {family_size} članova porodice")
    
    if owns_agricultural_land and agricultural_land_hectares > (max_agricultural_per_member * family_size):
        eligible = False
        max_allowed = max_agricultural_per_member * family_size
        ineligible_reasons.append(f"❌ Poljoprivredno zemljište ({agricultural_land_hectares} ha) prelazi limit od {max_allowed} ha")
    
    # 5. Check liquid assets (Article 7)
    max_liquid_assets = max_liquid_multiplier * avg_salary
    if liquid_assets_per_member > max_liquid_assets:
        eligible = False
        ineligible_reasons.append(f"❌ Likvidna sredstva po članu ({liquid_assets_per_member:,.0f} RSD) prelaze limit od {max_liquid_assets:,.0f} RSD")
    
    # 6. Check child-specific requirements
    if not children_live_in_serbia:
        eligible = False
        ineligible_reasons.append("❌ Sva deca moraju živeti u Srbiji")
    
    if not children_attend_school:
        eligible = False
        ineligible_reasons.append("❌ Sva deca školskog uzrasta moraju redovno pohađati školu")
    
    if not children_vaccinated:
        eligible = False
        ineligible_reasons.append("❌ Sva deca moraju biti vakcinisana prema propisima")
    
    # 7. Check care arrangements
    if children_in_social_care:
        eligible = False
        ineligible_reasons.append("❌ Deca ne smeju biti smeštena u ustanove socijalne zaštite")
    
    if not parent_has_parental_rights:
        eligible = False
        ineligible_reasons.append("❌ Roditelj mora imati potpuno roditeljsko pravo")
    
    # Generate response
    if eligible:
        response = "✅ **IMATE PRAVO na dečiji dodatak!**\n\n"
        response += "**Vaši podaci:**\n"
        response += f"- Državljanstvo: {'Srpsko' if citizenship_lower in ['serbian', 'srbija', 'srpski'] else 'Stalni boravak'}\n"
        response += f"- Starost: {claimant_age} godina\n"
        response += f"- Broj dece: {num_children}\n"
        response += f"- Veličina porodice: {family_size} članova\n"
        response += f"- Mesečni prihod: {monthly_income:,.0f} RSD"
        if applied_multiplier > 1.0:
            response += f" (limit: {income_threshold:,.0f} RSD"
            if single_parent:
                response += f" - uvećan {int((single_parent_multiplier - 1) * 100)}% za jednoroditeljske porodice"
            elif has_disabled_child:
                response += f" - uvećan {int((disabled_child_multiplier - 1) * 100)}% za porodice sa detetom sa invaliditetom"
            response += ")"
        response += "\n\n**Svi uslovi su ispunjeni.**"
        
        # Add next steps
        response += "\n\n**Sledeći koraci:**\n"
        response += "1. Podnesite zahtev u opštini prema mestu prebivališta\n"
        response += "2. Priložite potrebnu dokumentaciju\n"
        response += "3. Pratite status vašeg zahteva"
        
        # Show required documents from JSON
        required_docs = THRESHOLDS.get("required_documents", {})
        if required_docs:
            response += "\n\n**Potrebna dokumentacija:**\n"
            for category, docs in required_docs.items():
                if docs:
                    response += f"- {category.replace('_', ' ').title()}: {', '.join(docs)}\n"
    else:
        response = "❌ **NEMATE PRAVO na dečiji dodatak.**\n\n"
        response += "**Razlozi:**\n"
        response += "\n".join(ineligible_reasons)
        
        # Add advice if close to eligibility
        if monthly_income < income_threshold * 1.1:
            response += "\n\n💡 **Savet:** Vaš prihod je blizu granice. Razmotrite mogućnosti smanjenja prijavljenih prihoda."
    
    return response

# Create the structured tool
eligibility_tool = StructuredTool.from_function(
    func=check_child_allowance,
    name="check_child_allowance",
    description="Comprehensively check eligibility for Serbian child allowance based on all legal requirements",
    args_schema=ChildAllowanceInput,
    return_direct=False
)
