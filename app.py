# legislation_drafter_app.py
"""
Streamlit app: Draft legislation from plain‑English policy instructions using OpenAI o3.

How to run locally:
1. pip install streamlit openai python-dotenv
2. export OPENAI_API_KEY="your_key"  # or add to a .env file
3. streamlit run legislation_drafter_app.py
"""

import os
import streamlit as st
from openai import OpenAI, OpenAIError

# ------- Configuration ------- #
MODEL_NAME = "o3"  # OpenAI reasoning model

# Initialise OpenAI client
client = OpenAI()

# ------- Streamlit UI ------- #
st.set_page_config(page_title="Legislation Drafter", page_icon="📜", layout="centered")
st.title("📜 Legislative Drafting Assistant")

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
)

if st.button("✍️ Draft Bill", type="primary"):
    if not policy_instruction.strip():
        st.warning("Please enter a policy change.")
        st.stop()

    # Build the system + user prompt
    system_prompt = (
        "You are a professional legislative counsel. "
        "Write concise, legally‑sound statutory language in active voice. "
        "Keep scope narrowly tailored to the described policy change and include effective dates."
    )

    user_prompt = f"Draft legislation that implements the following policy change: {policy_instruction.strip()}"

    with st.spinner("Drafting…"):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            bill_text = response.choices[0].message.content.strip()
            st.subheader("Generated Bill")
            st.code(bill_text, language="markdown")
        except OpenAIError as e:
            st.error(f"OpenAI API error: {e}")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

st.markdown("---")

st.markdown(
    "<small>© 2025 • Powered by OpenAI o3 • Built with Streamlit</small>",
    unsafe_allow_html=True,
)
