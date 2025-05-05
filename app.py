# legislation_drafter_app.py
"""
Streamlit app: Draft legislation from PolicyEngine code or plain‑English policy instructions using OpenAI o3.

How to run locally:
1. pip install streamlit openai python-dotenv policyengine_us pyyaml
2. export OPENAI_API_KEY="your_key" # or add to a .env file
3. streamlit run app.py
"""
import os
import streamlit as st
from openai import OpenAI, OpenAIError

# Import our custom modules
from policy_parser import extract_reform_dict_from_code, parse_policy_reform, format_date_values, get_parameter_info
from policy_text_generator import generate_policy_text

def format_bill_text_html(bill_text):
    """
    Format the generated bill text as HTML with enhanced styling.
    
    Args:
        bill_text (str): The raw bill text from the LLM
        
    Returns:
        str: HTML-formatted bill text with line numbers and proper styling
    """
    # Split the text into lines
    lines = bill_text.split('\n')
    
    # Create HTML with line numbers and styling
    html_lines = []
    line_number = 1
    
    for line in lines:
        # Skip empty lines for line numbering but keep them in the output
        if line.strip():
            # Process special markdown formatting in the line
            line = line.replace('__', '<span class="bill-addition">')
            line = line.replace('__', '</span>')
            line = line.replace('[~~', '<span class="bill-deletion">')
            line = line.replace('~~]', '</span>')
            
            # Check for section headers and apply special styling
            if 'SECTION' in line and ':' in line:
                html_lines.append(f'<div class="bill-line section-header"><span class="line-number">{line_number}</span><span class="line-content">{line}</span></div>')
            # Check for enacting clause
            elif 'Be it enacted' in line:
                html_lines.append(f'<div class="bill-line enacting-clause"><span class="line-number">{line_number}</span><span class="line-content">{line}</span></div>')
            else:
                html_lines.append(f'<div class="bill-line"><span class="line-number">{line_number}</span><span class="line-content">{line}</span></div>')
            line_number += 1
        else:
            html_lines.append(f'<div class="bill-line"><span class="line-number"></span><span class="line-content">&nbsp;</span></div>')
    
    # Join the lines and wrap in a container
    html_content = '<div class="bill-container">' + '\n'.join(html_lines) + '</div>'
    
    return html_content

# Custom CSS for the bill display
bill_css = """
<style>
    .bill-container {
        font-family: 'Courier New', monospace;
        background-color: #f9f9f9;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        max-height: 600px;
        overflow-y: auto;
        position: relative;
    }
    
    .bill-header {
        text-align: center;
        margin-bottom: 20px;
    }
    
    .bill-title {
        font-size: 1.2em;
        font-weight: bold;
        margin-bottom: 10px;
    }
    
    .bill-line {
        display: flex;
        line-height: 1.6;
        margin-bottom: 2px;
    }
    
    .line-number {
        color: #888;
        text-align: right;
        padding-right: 10px;
        width: 30px;
        flex-shrink: 0;
        user-select: none;
    }
    
    .line-content {
        flex-grow: 1;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    
    .bill-addition {
        background-color: #e6ffe6;
        text-decoration: underline;
        color: #006600;
        font-weight: bold;
    }
    
    .bill-deletion {
        background-color: #ffe6e6;
        text-decoration: line-through;
        color: #990000;
    }
    
    .section-header {
        font-weight: bold;
        margin-top: 15px;
        margin-bottom: 10px;
    }
    
    .enacting-clause {
        font-style: italic;
        margin: 15px 0;
    }
    
    @media print {
        .bill-container {
            box-shadow: none;
            border: none;
            max-height: none;
        }
    }
</style>
"""

# ------- Configuration -------
MODEL_NAME = "gpt-4o"  # OpenAI reasoning model

# Define enhanced system prompt for bill generation
BILL_SYSTEM_PROMPT = """
You are a professional legislative counsel with expertise in drafting US federal legislation. Your task is to produce formally structured bill text that follows standard legislative formatting conventions.

Begin with a proper bill designation (H.R. for House bills) followed by a bill number placeholder.

Include a descriptive title that clearly indicates the purpose of the legislation.

Format the bill with the standard enacting clause: "Be it enacted by the Senate and House of Representatives of the United States of America in Congress assembled,"

Organize the content into properly numbered SECTIONS (capitalized) with descriptive headings.

When amending existing law:
- Use proper amendatory language ("Section X of Y is amended by...")
- Place new text in quotation marks
- For additions, use underline notation (represent this as __new text__ in markdown)
- For deletions, use brackets and strikethrough notation (represent this as [~~deleted text~~] in markdown)

Include definitions section when introducing new technical terms.

Include appropriate effective date language in the final section.

Use proper legislative language conventions:
- Write in the present tense
- Use "shall" for mandatory actions
- Use "may" for discretionary actions
- Be precise and unambiguous
- Use active voice
- Avoid abbreviations

Write concise, legally-sound statutory language that is narrowly tailored to the described policy change.
"""

# Initialize OpenAI client
client = OpenAI()

# ------- Streamlit UI -------
st.set_page_config(page_title="Legislation Drafter", page_icon="📜", layout="centered")
st.title("📜 Legislative Drafting Assistant")

# Create tabs for different input methods
tab1, tab2 = st.tabs(["PolicyEngine Code", "Plain English"])

# Tab 1: PolicyEngine Python Code Input
with tab1:
    st.markdown(
        """
        Enter PolicyEngine Python code and click **Generate Bill** to convert it to both plain English
        and formal legislative text.
        
        Example format:
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
        ```
        """
    )
    
    policy_code = st.text_area(
        "PolicyEngine Python Code",
        height=200,
    )
    
    if st.button("📝 Generate Bill", type="primary", key="generate_policy_bill"):
        if not policy_code.strip():
            st.warning("Please enter PolicyEngine Python code.")
            st.stop()
        
        try:
            # Extract the reform dictionary from the Python code
            reform_dict = extract_reform_dict_from_code(policy_code)
            
            # Parse the reform and generate text description
            reform_info = parse_policy_reform(reform_dict)
            policy_text = generate_policy_text(reform_info)
            
            # Display the generated text
            st.subheader("Generated Policy Text")
            st.write(policy_text)
            
            # Store the generated text and reform info in session state
            st.session_state.policy_instruction = policy_text
            st.session_state.reform_info = reform_info
            
            # Display collapsible sections with parameter details
            st.subheader("Parameter Details")
            for index, reform_item in enumerate(reform_info):
                param_path = reform_item["parameter"]
                with st.expander(f"Parameter: {param_path}"):
                    # Get the full parameter info from policyengine
                    param_info = get_parameter_info(param_path)
                    
                    # Display description
                    if "description" in param_info:
                        st.markdown(f"**Description:** {param_info['description']}")
                    
                    # Display values/brackets if available using json-safe values
                    if "brackets" in param_info:
                        st.markdown("**Brackets:**")
                        for bracket in param_info["brackets"]:
                            # Convert date objects to strings for JSON serialization
                            bracket_safe = format_date_values(bracket)
                            st.json(bracket_safe)
                    elif "values" in param_info:
                        st.markdown("**Values:**")
                        values_safe = format_date_values(param_info["values"])
                        st.json(values_safe)
                    
                    # Display metadata if available
                    if "metadata" in param_info:
                        st.markdown("**Metadata:**")
                        st.json(param_info["metadata"])
                    
                    # Display references if available
                    if "metadata" in param_info and "reference" in param_info["metadata"]:
                        st.markdown("**References:**")
                        for ref in param_info["metadata"]["reference"]:
                            if "href" in ref and "title" in ref:
                                st.markdown(f"- [{ref['title']}]({ref['href']})")
                            else:
                                st.json(ref)
            
            # Get the enhanced context from policy reform information
            enhanced_context = "Here is additional context about the parameters being modified:\n\n"
            
            for reform_item in reform_info:
                param_path = reform_item["parameter"]
                param_info = get_parameter_info(param_path)
                
                # Add parameter path and description
                enhanced_context += f"Parameter: {param_path}\n"
                if "description" in param_info:
                    enhanced_context += f"Description: {param_info['description']}\n"
                
                # Add current values information
                if "brackets" in param_info:
                    enhanced_context += "Current brackets:\n"
                    for bracket in param_info["brackets"]:
                        # Convert date objects to strings in thresholds and amounts
                        threshold_str = str(format_date_values(bracket.get('threshold', {})))
                        amount_str = str(format_date_values(bracket.get('amount', {})))
                        enhanced_context += f"- Threshold: {threshold_str}\n"
                        enhanced_context += f"  Amount: {amount_str}\n"
                elif "values" in param_info:
                    # Convert date objects to strings in values
                    values_str = str(format_date_values(param_info['values']))
                    enhanced_context += f"Current values: {values_str}\n"
                
                # Add metadata
                if "metadata" in param_info and "type" in param_info["metadata"]:
                    enhanced_context += f"Type: {param_info['metadata']['type']}\n"
                
                # Add references
                if "metadata" in param_info and "reference" in param_info["metadata"]:
                    enhanced_context += "Legal references:\n"
                    for ref in param_info["metadata"]["reference"]:
                        if "title" in ref:
                            enhanced_context += f"- {ref['title']}"
                            if "href" in ref:
                                enhanced_context += f" ({ref['href']})"
                            enhanced_context += "\n"
                
                # Add proposed change
                enhanced_context += f"Proposed change: {reform_item['new_value']} (effective {reform_item['start_date']} to {reform_item['end_date']})\n\n"
            
            # Build the system + user prompt
            system_prompt = BILL_SYSTEM_PROMPT
            
            user_prompt = f"Draft legislation that implements the following policy change:\n\n{policy_text}\n\n{enhanced_context}"
            
            with st.spinner("Drafting bill..."):
                try:
                    response = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                    )
                    bill_text = response.choices[0].message.content.strip()
                    
                    # Display the bill with enhanced styling
                    st.subheader("Generated Bill")
                    st.markdown(bill_css, unsafe_allow_html=True)
                    st.markdown(format_bill_text_html(bill_text), unsafe_allow_html=True)
                    
                    # Also keep the plain text version for copying
                    with st.expander("Show plain text version (for copying)"):
                        st.code(bill_text, language="markdown")
                        
                except OpenAIError as e:
                    st.error(f"OpenAI API error: {e}")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")
                
        except ValueError as e:
            st.error(f"Error extracting reform: {str(e)}")
        except Exception as e:
            st.error(f"Error processing PolicyEngine reform: {str(e)}")

# Tab 2: Plain English Input
with tab2:
    st.markdown(
        """
        Enter a plain‑English policy description and click **Generate Bill**.
        The app calls the OpenAI model to return neutral, formal legislative text.
        
        *Examples you can paste →*
        - Draft a bill that changes the SNAP expected food contribution to 40%.
        - Draft a bill that sets the maximum Child Tax Credit amount in 2025 to $2,500.
        - Draft legislation raising Montana's top marginal income‑tax rate to 7% starting in 2026.
        """
    )
    
    policy_instruction = st.text_area(
        "Policy change (plain language)",
        height=160,
    )
    
    if st.button("📝 Generate Bill", type="primary", key="generate_plain_bill"):
        if not policy_instruction.strip():
            st.warning("Please enter a policy change.")
            st.stop()
        
        # Build the system + user prompt
        system_prompt = BILL_SYSTEM_PROMPT
        
        user_prompt = f"Draft legislation that implements the following policy change:\n\n{policy_instruction.strip()}"
        
        with st.spinner("Drafting bill..."):
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                bill_text = response.choices[0].message.content.strip()
                
                # Display the bill with enhanced styling
                st.subheader("Generated Bill")
                st.markdown(bill_css, unsafe_allow_html=True)
                st.markdown(format_bill_text_html(bill_text), unsafe_allow_html=True)
                
                # Also keep the plain text version for copying
                with st.expander("Show plain text version (for copying)"):
                    st.code(bill_text, language="markdown")
                    
            except OpenAIError as e:
                st.error(f"OpenAI API error: {e}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")
                
# Remove the common section for bill drafting since we've integrated it into each tab

st.markdown("---")

st.markdown(
    "<small>© 2025 • Powered by OpenAI GPT-4o • Built with Streamlit</small>",
    unsafe_allow_html=True,
)