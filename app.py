# app.py
import streamlit as st
from app_tools import RagEngine

# Page config
st.set_page_config(
    page_icon="🤖",
    page_title="Ask Gamma",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items=None
)

# Initialize session state
if 'rag_engine' not in st.session_state:
    st.session_state.rag_engine = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'chat_started' not in st.session_state:
    st.session_state.chat_started = False

# Sidebar controls
with st.sidebar:
    st.header("🅞🆇 Z 🅴🅴", divider="grey")
    chat_type = st.selectbox(
        ":grey-background[Type du Chat]",
        ["Chat Simple", "Chat avec Gamma", "Ask Stocks"]
    )

    # RAG-specific filters
    if chat_type == "Chat avec Gamma":
        STATUS_OPTIONS = ["Null", "OK", "NOK"]
        APP_OPTIONS = ["Null", "App_Zee", "App_Alpha", "App_Beta", "App_Gamma", "App_Delta"]
        with st.expander(":gray[Filtres : SSA / Statut MEP]", expanded=True):
            app_filter = st.selectbox("Application MEP", APP_OPTIONS, key="app_filter")
            status_filter = st.selectbox("Statut MEP", STATUS_OPTIONS, key="status_filter")

    # Session control buttons
    if not st.session_state.chat_started:
        if st.button("Démarrer La Session Chat", use_container_width=True):
            st.session_state.rag_engine = RagEngine()
            # chat simple
            if chat_type == "Chat Simple":
                st.session_state.rag_engine.create_simple_chat()
                hello_message = ":sparkles: Bonjour, Comment puis-je vous aider ?"
            # chat RAG Stocks
            if chat_type == "Ask Stocks":
                st.session_state.rag_engine.create_stx_rag_chat()
                hello_message = ":sparkles: Hello, How can I help with the Stocks ?"
            # chat RAG MEP
            if chat_type == "Chat avec Gamma":
                # Pass filters only if they're not "Null"
                app_filter_value = None if app_filter == "Null" else app_filter
                status_filter_value = None if status_filter == "Null" else status_filter
                st.session_state.rag_engine.create_rag_chat(
                    app_filter=app_filter_value,
                    status_filter=status_filter_value
                )
                hello_message = ":sparkles: Bonjour, Avez-vous des questions sur les MEP ?"
                
            st.session_state.messages = [
                {"role": "assistant", "content": hello_message}
            ]
            st.session_state.chat_started = True
            st.rerun()
    else:
        if st.button("Terminer La Session", use_container_width=True, type="primary"):
            if st.session_state.rag_engine:
                st.session_state.rag_engine.reset()
            st.session_state.rag_engine = None
            st.session_state.messages = []
            st.session_state.chat_started = False
            st.rerun()

# Main chat interface
st.subheader("၊၊||၊ Chat🅱🅞🆃 ☰", divider="grey")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Enter your message", disabled=not st.session_state.rag_engine):
    # Add user message to chat history
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Generating response..."):
            response = st.session_state.rag_engine.chat_engine.chat(prompt)
            #st.markdown(response.response)
            response_str = ""
            response_container = st.empty()
            for token in response.response:
                response_str += token
                response_container.markdown(response_str)
            
        # Display sources for RAG chat
        if hasattr(response, 'source_nodes'):
            with st.expander("📚 🔗 Sources"):
                # Get all unique metadata keys from all nodes
                all_metadata_keys = set()
                for node in response.source_nodes:
                    all_metadata_keys.update(node.metadata.keys())
                
                # Create sources data with all metadata fields
                sources_data = []
                for node in response.source_nodes:
                    node_data = {
                        key: node.metadata.get(key, "N/A") for key in all_metadata_keys
                    }
                    # Add score separately since it's not in metadata
                    node_data["relevance_score"] = node.score
                    sources_data.append(node_data)
                
                st.table(sources_data)

    # Add assistant response to chat history
    st.session_state.messages.append(
        {"role": "assistant", "content": response.response}
    )
