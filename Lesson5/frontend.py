
import os
import streamlit as st
from multi_agent import build_graph, OLLAMA_MODEL

st.set_page_config(
    page_title="Multi-Agent Support System",
    page_icon="🛠️",
    layout="centered",
)

st.title("🛠️ Multi-Agent Support System")
st.caption(f"Supervisor → IT Agent / Finance Agent · running on local Ollama model `{OLLAMA_MODEL}`")

@st.cache_resource
def get_app():
    return build_graph()


app = get_app()

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.subheader("About")
    st.write(
        "This app routes your question to either the **IT Agent** or the "
        "**Finance Agent** via a Supervisor classifier. The Finance Agent "
        "can call `ReadFile` (internal docs) and `WebSearch` (DuckDuckGo)."
    )
    st.divider()
    if st.button("🗑️ Clear chat"):
        st.session_state.messages = []
        st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and msg.get("category"):
            st.caption(f"Routed to **{msg['category']} Agent**")
        st.markdown(msg["content"])

user_query = st.chat_input("Ask an IT or Finance question…")

if user_query:

    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Routing and thinking…"):
            try:
                result = app.invoke(
                    {"query": user_query, "category": None, "response": None}
                )
                category = result.get("category", "Unknown")
                response = result.get("response", "(no response)")
            except Exception as exc:
                category = None
                response = (
                    f"⚠️ Error while running the graph: `{exc}`\n\n"
                    "Make sure Ollama is running locally (`ollama serve`) "
                    "and that the model is pulled (`ollama pull llama3.1`)."
                )

        if category:
            st.caption(f"Routed to **{category} Agent**")
        st.markdown(response)

    st.session_state.messages.append(
        {"role": "assistant", "content": response, "category": category}
    )