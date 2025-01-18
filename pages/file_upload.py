import streamlit as st
import pandas as pd
from functions.multi_pages import multi_page

st.set_page_config(
    page_title="データ分析アプリケーション",
    page_icon=":computer:",
    layout="wide",
    initial_sidebar_state="auto"
)

multi_page()

# セッションステートの初期化
if 'df' not in st.session_state:
    st.session_state.df = None

st.title("CSVファイルアップローダー")
uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type=["csv"])

if uploaded_file is not None:
    # アップロード結果の可視化
    df = pd.read_csv(uploaded_file)
    st.write("アップロードされたデータ:")
    st.dataframe(df)
    
    st.write("データの概要:")
    st.dataframe(df.describe(include='all'))

    # データをセッションステートに保存
    st.session_state.df = df

    # カラム名を保存
    # 数値型のカラム名のリスト
    st.session_state.numeric_columns = df.select_dtypes(include=['number']).columns.tolist()

    # 数値型以外のカラム名のリスト
    st.session_state.non_numeric_columns = df.select_dtypes(exclude=['number']).columns.tolist()

    st.write("数値型のカラム:", st.session_state.numeric_columns)
    st.write("数値型以外のカラム:", st.session_state.non_numeric_columns)