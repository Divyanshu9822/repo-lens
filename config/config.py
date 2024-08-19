import streamlit as st

TOOL_CALL_MODEL = "llama3-groq-70b-8192-tool-use-preview"
GITHUB_CLIENT_ID = st.secrets["GITHUB_CLIENT_ID"]  
GITHUB_CLIENT_SECRET = st.secrets["GITHUB_CLIENT_SECRET"]  
REDIRECT_URI = st.secrets["REDIRECT_URI"]

