import streamlit as st
import pandas as pd
from functions.multi_pages import multi_page

###########################
# ページの設定
###########################
st.set_page_config(
    page_title="データ分析アプリケーション",
    page_icon=":computer:",
    layout="wide",
    initial_sidebar_state="auto"
)

###########################
# サイドバーの設定
###########################
multi_page()

###########################
# コンテンツ
###########################
# セッションステートの初期化
if 'df' not in st.session_state:
    st.session_state.df = None

st.title("CSVファイルアップローダー")
uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type=["csv"])

if uploaded_file is not None:
    # アップロード結果の可視化
    df = pd.read_csv(uploaded_file)
    st.write("アップロードされたデータのサイズ:", df.shape)
    st.dataframe(df)

    # データをセッションステートに保存
    st.session_state.df = df