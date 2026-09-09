import os
import time

import streamlit as st
from dotenv import load_dotenv
from google import genai


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AI Code Explainer",
    page_icon="⚡",
    layout="wide"
)


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        api_key = None

if not api_key:
    st.error("GEMINI_API_KEY is missing.")
    st.stop()

client = genai.Client(api_key=api_key)

MODEL = "gemini-3.5-flash-lite"


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main {
        background-color: #0b0f14;
    }

    .block-container {
        max-width: 1100px;
        padding-top: 2rem;
    }

    .title {
        font-size: 42px;
        font-weight: 700;
    }

    .subtitle {
        color: #8b949e;
        font-size: 18px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="title">⚡ AI Code Explainer</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Understand. Learn. Improve.</div>',
    unsafe_allow_html=True
)

st.divider()


# =========================================================
# LANGUAGE SELECTION
# =========================================================

language = st.selectbox(
    "Programming Language",
    [
        "Python",
        "JavaScript",
        "Java",
        "C",
        "C++",
        "C#"
    ]
)


# =========================================================
# CODE INPUT
# =========================================================

code = st.text_area(
    "💻 Code Input",
    height=350,
    placeholder="Paste your code here..."
)


# =========================================================
# BUTTONS
# =========================================================

col1, col2, col3 = st.columns([1, 1, 4])

with col1:
    explain_button = st.button(
        "✨ Explain Code",
        use_container_width=True
    )

with col2:
    bugs_button = st.button(
        "🐛 Find Bugs",
        use_container_width=True
    )


# =========================================================
# PROMPT GENERATION
# =========================================================

def create_prompt(task: str, language: str, code: str) -> str:

    if task == "explain":

        return f"""
You are an expert programming teacher.

Analyze the following {language} code.

Give the response in this exact structure:

## Explanation
Explain what the code does in simple language.

## How It Works
Explain the important parts step by step.

## Potential Issues
Mention bugs, errors, or risky practices if there are any.
If there are no issues, say "No obvious issues found."

## Improvements
Suggest useful improvements.

## Complexity
Give the approximate time and space complexity if applicable.

Code:

{code}
"""

    return f"""
You are a highly experienced software engineer and professional
code reviewer.

Analyze the following {language} code specifically for bugs,
errors, edge cases, and potential security problems.

Give the response in this exact structure:

## Bugs Found
List every actual bug you can identify.
If there are no bugs, say "No obvious bugs found."

## Edge Cases
Mention inputs or situations that could cause unexpected behavior.

## Security Issues
Mention security vulnerabilities if applicable.
If there are none, say "No obvious security issues found."

## Recommended Fixes
Explain how to fix each important problem.

## Corrected Code
Provide an improved version of the code only if changes are needed.

Code:

{code}
"""


# =========================================================
# GEMINI ANALYSIS
# =========================================================

def analyze_code(task: str, language: str, code: str) -> str:

    prompt = create_prompt(task, language, code)

    last_error = None

    # Try up to 3 times for temporary 503 errors
    for attempt in range(3):

        try:

            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )

            if response.text:
                return response.text

            raise Exception("Gemini returned an empty response.")

        except Exception as error:

            last_error = error
            error_text = str(error)

            # Temporary service availability problem
            if "503" in error_text or "UNAVAILABLE" in error_text:

                if attempt < 2:
                    time.sleep(2 ** (attempt + 1))
                    continue

                raise Exception(
                    "Gemini is temporarily busy. "
                    "Please try again in a few seconds."
                ) from error

            # Rate limit
            if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:

                raise Exception(
                    "Gemini API rate limit reached. "
                    "Please wait a little and try again."
                ) from error

            # Other errors
            raise error

    raise Exception(
        "Unable to get a response from Gemini."
    ) from last_error


# =========================================================
# PROCESS REQUEST
# =========================================================

if explain_button or bugs_button:

    if not code.strip():

        st.warning("Please paste some code first.")

    else:

        task = "explain" if explain_button else "bugs"

        with st.spinner("🤖 AI is analyzing your code..."):

            try:

                result = analyze_code(
                    task,
                    language,
                    code
                )

                st.divider()

                st.subheader("🧠 AI Analysis")

                st.markdown(result)

            except Exception as error:

                st.error(
                    f"Something went wrong: {error}"
                )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Built with FastAPI + Gemini AI + Streamlit"
)