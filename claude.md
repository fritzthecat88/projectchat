# Serbian Child Allowance Eligibility Chatbot

## Project Overview
This is a Streamlit-based chatbot that helps Serbian citizens determine their eligibility for child allowance (dečiji dodatak) based on Serbian law "Zakon o finansijskoj podršci породици sa decom".

## Current Status
- ✅ Basic chatbot working with LangChain and OpenAI
- ✅ Simple eligibility checking (age, income, number of children)
- ⚠️ Only checks 3 basic conditions, but law has many more requirements
- 🔄 Need to implement comprehensive eligibility checking

## Technical Stack
- **Frontend**: Streamlit
- **LLM Framework**: LangChain with OpenAI GPT-3.5
- **Language**: Python 3.11
- **Deployment**: Streamlit Cloud
- **Dependencies**: See environment.yml

## Key Files
- `chattest.py` - Main Streamlit chat interface
- `eligibility_tool.py` - LangChain tool for checking eligibility
- `thresholds.json` - Configurable thresholds and rules
- `environment.yml` - Conda environment specification

## Requirements for Full Implementation

### Legal Requirements to Check (from Serbian law):
1. **Citizenship/Residence** (Article 26)
   - Serbian citizen with residence in Serbia OR
   - Foreign citizen with permanent resident status

2. **Property Ownership** (Articles 7-8)
   - Max 1 room per family member + 1 extra room
   - Agricultural families: max 2 hectares per member
   - No additional properties allowed
   - Liquid assets < 2 average salaries per member

3. **Child Requirements** (Article 26)
   - Children must live and attend school in Serbia
   - Must attend preschool preparation program
   - Regular school attendance required
   - Vaccination according to Serbian regulations
   - Age limits: up to 20 (21 with valid reasons, 26 for disabled)

4. **Income Calculation** (Article 30)
   - Complex income calculation including cadastral income
   - Income thresholds increase for:
     - Single parents (+30% or +20% depending on category)
     - Families with disabled children (+20%)
     - Foster parents (+20%)

5. **Direct Care** (Article 27)
   - Parent must directly care for child
   - Child not in social care institution
   - Parent has full parental rights

### Chatbot Behavior Requirements
- Ask questions in conversational Serbian
- Collect all required information before determining eligibility
- Provide clear explanations for eligibility/ineligibility
- Show which documents are needed
- Handle edge cases gracefully

## Development Guidelines
- Keep all configurable values in `thresholds.json`
- Use Serbian language for user-facing messages
- Maintain conversation context throughout the session
- Validate inputs appropriately
- Log decisions for debugging

## Testing Scenarios
1. Basic eligible family (2 parents, 2 kids, low income)
2. Single parent with increased threshold
3. Family with disabled child
4. Foreign permanent resident
5. Family exceeding property limits
6. Unvaccinated children (should be ineligible)
7. Children not attending school (should be ineligible)

## Future Enhancements
- [ ] Add document upload functionality
- [ ] Integration with government databases (when available)
- [ ] Multi-language support (Serbian/English)
- [ ] Save/resume application functionality
- [ ] Generate PDF application forms

## Important Notes
- OpenAI API key stored in Streamlit secrets
- No personal data should be stored permanently
- All amounts in RSD (Serbian Dinars)
- Thresholds updated twice yearly (January 1 and July 1)

## References
- Law: "Zakon o finansijskoj podršci породици sa decom"
- Official Gazette: Službeni glasnik RS, br. 113/2017, 50/2018, 66/2021, 130/2021, 62/2023
