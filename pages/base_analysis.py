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

st.title("基本的な集計・グラフの描画")
## dfがセッションステートに保存されていない or セッションステートに存在するが空のファイルの場合
if 'df' not in st.session_state or st.session_state.df is None:
    st.write("CSVファイルをアップロードしてください。")
else:
    # タブの作成
    tab_list = st.tabs(
        ["データの型",
         "1変数の統計量",
         "2変数(量的変数×量的変数)",
         "2変数(量的変数×質的変数)",]
        )

    with tab_list[0]:
        st.header("データの型")
        st.write(st.session_state.df.dtypes)

    with tab_list[1]:
        st.header("1変数の統計量")
        st.write(st.session_state.df.describe())
        st.write(st.session_state.df.describe(exclude="number"))
    with tab_list[2]:
        st.header("2変数(量的変数×量的変数)")
    with tab_list[3]:
        st.header("2変数(量的変数×質的変数)")