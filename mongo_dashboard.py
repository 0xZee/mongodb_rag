import streamlit as st
from pymongo import MongoClient
import pandas as pd

st.set_page_config(layout="wide", page_title="MongoDB Explorer")

# Initialize session state variables
if 'client' not in st.session_state:
    st.session_state.client = None
if 'status' not in st.session_state:
    st.session_state.status = 'Not connected'
if 'selected_db' not in st.session_state:
    st.session_state.selected_db = None
if 'selected_collection' not in st.session_state:
    st.session_state.selected_collection = None

# MongoDB Connection Function
def connect_to_mongodb(cluster):
    uri = f"mongodb+srv://{st.secrets.mdb_user}:{st.secrets.mdb_pwd}@{cluster}.d1jsd.mongodb.net/?retryWrites=true&w=majority&appName=zee"
    try:
        client = MongoClient(uri)
        client.admin.command('ping')
        st.session_state.status = 'Connected'
        return client
    except Exception as e:
        st.session_state.status = f"Failed to connect: {e}"
        return None

# Function to get collection data
def get_collection_data(filter_key=None, filter_value=None):
    if st.session_state.client and st.session_state.selected_db and st.session_state.selected_collection:
        db = st.session_state.client[st.session_state.selected_db]
        collection = db[st.session_state.selected_collection]
        query = {filter_key: filter_value} if filter_key and filter_value else {}
        data = list(collection.find(query, {'_id': 0}))
        return pd.DataFrame(data)
    return pd.DataFrame()

# Sidebar
with st.sidebar:
    st.header("🌍 MongoDB Explorer", divider='grey')

    selected_cluster = st.selectbox("📊 Atlas MongoDB Cluster", ['zee-cluster'])

    if not st.session_state.client:
        st.session_state.client = connect_to_mongodb(selected_cluster)

    if st.session_state.client:
        databases = st.session_state.client.list_database_names()
        st.session_state.selected_db = st.selectbox('📁 Select Database', databases)

        if st.session_state.selected_db:
            db = st.session_state.client[st.session_state.selected_db]
            collections = db.list_collection_names()
            st.session_state.selected_collection = st.selectbox('📑 Select Collection', collections)

            st.json(collections, expanded=False)

    # Status Display
    st.header("📊 Connection Status", divider='grey')
    status_data = {
        'Status': [st.session_state.status],
        'Cluster': [selected_cluster],
        'Database': [st.session_state.selected_db],
        'Collection': [st.session_state.selected_collection]
    }
    st.dataframe(pd.DataFrame(status_data), use_container_width=True, hide_index=True)

# Main content
st.header("🔍 MongoDB Data Explorer", divider='grey')

# Filter form
with st.form("filter_form"):
    st.subheader("🔎 Filter Data", divider='grey')
    col1, col2 = st.columns(2)
    with col1:
        filter_key = st.text_input("🔑 Filter Key")
    with col2:
        filter_value = st.text_input("🔖 Filter Value")

    submit_button = st.form_submit_button("📊 Display Collection Data", use_container_width=True)

    if submit_button:
        df = get_collection_data(filter_key, filter_value)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No data found in the selected collection or with the specified filter.")

st.caption("🌍 github.com/0xZee/")
