# app.py
"""
Streamlit app: Draft legislation from PolicyEngine JSON using OpenAI o3.

How to run locally:
1. pip install streamlit openai python-dotenv
2. export OPENAI_API_KEY="your_key"  # or add to a .env file
3. streamlit run app.py
"""

import os
import streamlit as st
from openai import OpenAI, OpenAIError
from utils.policy_parser import parse_policy_json, PolicyParseError
from utils.text_generator import generate_policy_text, TextGenerationError
from utils.bill_generator import generate_bill_text, BillGenerationError

# ------- Configuration ------- #
MODEL_NAME = "gpt-4o"  # OpenAI reasoning model

# Initialize OpenAI client
client = OpenAI()

# ------- Helper Functions ------- #
def process_policy_engine_json(json_code, debug_mode=False):
    """Process PolicyEngine JSON and return policy text and bill text."""
    try:
        # Parse the PolicyEngine JSON
        parsed_policy = parse_policy_json(json_code)
        
        # Generate human-readable policy text
        policy_text = generate_policy_text(parsed_policy)
        
        # Build the prompts for bill generation
        system_prompt = (
            "You are a professional legislative counsel. "
            "Write concise, legally‑sound statutory language in active voice. "
            "Keep scope narrowly tailored to the described policy change and include effective dates."
        )
        
        user_prompt = f"Draft legislation that implements the following policy change: {policy_text.strip()}"
        
        # Store prompts if debug mode is on
        debug_info = {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "parsed_policy": parsed_policy
        } if debug_mode else None
        
        # Generate bill text
        bill_text = generate_bill_text(policy_text, MODEL_NAME)
        
        return policy_text, bill_text, debug_info
    except (PolicyParseError, TextGenerationError, BillGenerationError) as e:
        raise Exception(f"Error processing policy: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}")

# ------- Streamlit UI ------- #
st.set_page_config(page_title="Legislation Drafter", page_icon="📜", layout="centered")
st.title("📜 Legislative Drafting Assistant")

# Add sidebar with debug toggle
with st.sidebar:
    st.title("Settings")
    debug_mode = st.toggle("Debug Mode", value=False, 
                          help="Show prompts sent to the LLM")

# Create tabs for different input methods
tab1, tab2 = st.tabs(["Plain Text Input", "PolicyEngine JSON Input"])

with tab1:
    st.markdown(
        """
    Enter a plain‑English policy description and click **Draft Bill**. 
    The app calls the **OpenAI o3** model to return neutral, formal legislative text.

    *Examples you can paste →*
    - Draft a bill that changes the SNAP expected food contribution to 40%.
    - Draft a bill that sets the maximum Child Tax Credit amount in 2025 to $2,500.
    - Draft legislation raising Montana's top marginal income‑tax rate to 7% starting in 2026.
        """,
        unsafe_allow_html=True,
    )

    policy_instruction = st.text_area(
        "Policy change (plain language)",
        height=160,
        key="plain_text_input"
    )

    if st.button("✍️ Draft Bill", key="plain_text_button", type="primary"):
        if not policy_instruction.strip():
            st.warning("Please enter a policy change.")
            st.stop()

        # Process plain text input directly
        with st.spinner("Drafting…"):
            try:
                # Use the existing bill generation directly
                if debug_mode:
                    bill_text, prompts = generate_bill_text(policy_instruction, MODEL_NAME, return_prompts=True)
                    
                    st.subheader("Generated Bill")
                    st.code(bill_text, language="markdown")
                    
                    # Show debug information
                    with st.expander("Debug Information", expanded=True):
                        st.subheader("Prompts Sent to the LLM")
                        st.write("**System Prompt:**")
                        st.code(prompts["system_prompt"])
                        st.write("**User Prompt:**")
                        st.code(prompts["user_prompt"])
                else:
                    bill_text = generate_bill_text(policy_instruction, MODEL_NAME)
                    st.subheader("Generated Bill")
                    st.code(bill_text, language="markdown")
            except Exception as e:
                st.error(f"Error: {e}")

with tab2:
    st.markdown(
        """
    Enter PolicyEngine JSON/Python code and click **Process & Draft Bill**. 
    The app will:
    1. Parse the PolicyEngine code
    2. Convert it to plain-English policy description
    3. Generate formal legislative text

    *Example format:*
    ```python
    from policyengine_us import Microsimulation
    from policyengine_core.reforms import Reform
    reform = Reform.from_dict({
      "gov.irs.credits.ctc.amount.base[0].amount": {
        "2025-01-01.2100-12-31": 2500
      }
    }, country_id="us")
    baseline = Microsimulation()
    reformed = Microsimulation(reform=reform)
    baseline_income = baseline.calculate("household_net_income", period=2025)
    reformed_income = reformed.calculate("household_net_income", period=2025)
    difference_income = reformed_income - baseline_income
    ```
        """,
        unsafe_allow_html=True,
    )

    policy_engine_code = st.text_area(
        "PolicyEngine JSON/Python code",
        height=300,
        key="policy_engine_input"
    )

    if st.button("🔄 Process & Draft Bill", key="policy_engine_button", type="primary"):
        if not policy_engine_code.strip():
            st.warning("Please enter PolicyEngine code.")
            st.stop()

        # Process PolicyEngine JSON input
        with st.spinner("Processing and drafting…"):
            try:
                # Process the PolicyEngine JSON with debug mode if enabled
                policy_text, bill_text, debug_info = process_policy_engine_json(
                    policy_engine_code, 
                    debug_mode=debug_mode
                )
                
                # Display results
                st.subheader("Generated Policy Description")
                st.write(policy_text)
                
                st.subheader("Generated Bill")
                st.code(bill_text, language="markdown")
                
                # Show debug information if enabled
                if debug_mode and debug_info:
                    with st.expander("Debug Information", expanded=True):
                        st.subheader("Prompts Sent to the LLM")
                        st.write("**System Prompt:**")
                        st.code(debug_info["system_prompt"])
                        st.write("**User Prompt:**")
                        st.code(debug_info["user_prompt"])
                        
                        st.subheader("Parsed Policy Data")
                        st.json(debug_info["parsed_policy"])
            except Exception as e:
                st.error(f"Error: {e}")

# Additional UI elements
st.markdown("---")
with st.expander("How it works"):
    st.markdown(
        """
        This application helps convert policy changes into formal legislative language:
        
        1. **PolicyEngine JSON to Text**: 
           - Parses PolicyEngine JSON/Python code
           - Extracts parameter changes and their values
           - Generates a human-readable policy description
           
        2. **Text to Legislative Bill**:
           - Takes the policy description
           - Uses OpenAI's o3 model to draft formal legislative language
           - Returns properly formatted bill text
        
        The application can be used with either direct policy descriptions or with 
        PolicyEngine code for more precise policy modeling.
        """
    )

# Footer
st.markdown("---")
st.markdown(
    "<small>© 2025 • Powered by OpenAI o3 and PolicyEngine • Built with Streamlit</small>",
    unsafe_allow_html=True,
)