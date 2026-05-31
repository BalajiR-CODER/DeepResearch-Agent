import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000"

st.set_page_config(page_title="DeepResearch Agent", layout="wide")
st.title("🔬 DeepResearch Agent")
st.caption("Ask any research question — the agent searches the web and writes a report.")

query = st.text_area(
    "Enter your research question:",
    height=100,
    placeholder="e.g. What are the latest developments in India's semiconductor industry?"
)

if st.button("🚀 Run Research", disabled=not query):
    st.markdown("---")
    status = st.status("Agent is working...", expanded=True)

    with status:
        st.write("🧠 Planning sub-queries...")
        st.write("🔍 Searching the web for each sub-query...")
        st.write("📄 Reading and extracting content from sources...")
        st.write("✍️ Synthesizing findings into a report...")

    try:
        response = requests.post(
            f"{BACKEND_URL}/research",
            json={"query": query},
            timeout=120
        )
        if response.status_code == 200:
            status.update(label="✅ Research complete!", state="complete", expanded=False)
            report = response.json()["report"]
            st.markdown(report)
        else:
            status.update(label="❌ Something went wrong", state="error", expanded=False)
            st.error(f"Backend error: {response.text}")
    except requests.exceptions.Timeout:
        status.update(label="❌ Request timed out", state="error", expanded=False)
        st.error("The research took too long. Try a more specific question.")
    except requests.exceptions.ConnectionError:
        status.update(label="❌ Could not connect", state="error", expanded=False)
        st.error("Could not connect to backend. Is `uvicorn backend.app:app --reload` running?")
    except Exception as e:
        status.update(label="❌ Unexpected error", state="error", expanded=False)
        st.error(f"Error: {e}")