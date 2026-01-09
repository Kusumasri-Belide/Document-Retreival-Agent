import streamlit as st
import requests

st.title("📘 Azure Document Agent")
query = st.text_input("Ask a question about your documents:")

if st.button("Ask"):
    if not query.strip():
        st.warning("Please enter a question.")
    else:
        try:
            resp = requests.post(
                "http://127.0.0.1:8001/ask",
                json={"question": query},
                timeout=30,
            )
            if resp.status_code != 200:
                st.error(f"API error {resp.status_code}")
                st.code(resp.text or "<empty response>", language="text")
            else:
                try:
                    data = resp.json()
                    st.write("### 🧠 Answer:")
                    st.write(data.get("answer", "(no answer field)"))
                except ValueError:
                    st.error("Response is not valid JSON.")
                    st.code(resp.text or "<empty response>", language="text")
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")
            st.info("Is the API running at http://127.0.0.1:8000 and reachable?")