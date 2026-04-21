import streamlit as st
from llm import app  # import your LangGraph app
from langgraph.checkpoint.memory import MemorySaver

# Thread config (same as your backend)
thread_config = {"configurable": {"thread_id": "post_v1"}}

st.set_page_config(page_title="LinkedIn AI Poster", layout="centered")

st.title("🤖 LinkedIn AI Post Generator")

# Session state to persist data
if "generated" not in st.session_state:
    st.session_state.generated = False

if "content" not in st.session_state:
    st.session_state.content = ""

# Input
query = st.text_area("Enter your LinkedIn post topic:")

# Generate button
if st.button("Generate Post"):
    if query.strip() == "":
        st.warning("Please enter a topic.")
    else:
        app.invoke({"query": query}, thread_config)

        state = app.get_state(thread_config)
        st.session_state.content = state.values["content"]
        st.session_state.generated = True

# Show generated post
if st.session_state.generated:
    st.subheader("📄 Draft Post")
    st.text_area("Generated Content", st.session_state.content, height=200)

    col1, col2 = st.columns(2)

    # Approve
    with col1:
        if st.button("✅ Approve & Post"):
            app.update_state(
                thread_config,
                {"approval_status": "approved"},
                as_node="writer"
            )
            app.invoke(None, thread_config)
            st.success("Posted to LinkedIn!")

    # Reject
    with col2:
        if st.button("❌ Reject"):
            st.error("Post rejected.")
            st.session_state.generated = False