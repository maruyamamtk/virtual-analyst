import streamlit as st

def multi_page():
    with st.sidebar:
        st.page_link("main.py", label="ホーム", icon="🏠")
        st.page_link("pages/file_upload.py", label="csvアップロード", icon="📁")
        st.page_link("pages/change_datatype.py", label="データの型変換", icon="🔄")
        st.page_link("pages/filtering.py", label="データのフィルター", icon="🔽")
        st.page_link("pages/base_analysis.py", label="基礎集計", icon="📊")
        st.page_link("pages/chatbot.py", label="チャットボット", icon="🤖")