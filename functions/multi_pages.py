import streamlit as st

def multi_page():
    with st.sidebar:
        st.page_link("main.py", label="ホーム", icon="🏠")
        st.page_link("pages/file_upload.py", label="csvアップロード", icon="📁")
        st.page_link("pages/base_analysis.py", label="基礎集計", icon="📊")