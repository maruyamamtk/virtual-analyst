import streamlit as st
import pandas as pd
from pygwalker.api.streamlit import StreamlitRenderer
 
# 環境変数が設定されていない場合、以下のコマンドを実行する必要がある
# python -m streamlit run .\streamlit_app.py

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
st.sidebar.title("メニュー")
# セッションステートの初期化
if 'page' not in st.session_state:
    st.session_state.page = "ホーム🏠"
if 'df' not in st.session_state:
    st.session_state.df = None

# ページ選択
page = st.sidebar.radio("ページを選択してください",
                             ["ホーム🏠", "ファイルアップロード📂", "基礎集計📊"],
                             index=["ホーム🏠", "ファイルアップロード📂", "基礎集計📊"].index(st.session_state.page)
                            )

# 選択されたページをセッションステートに保存
st.session_state.page = page

###########################
# ページの表示
###########################
if st.session_state.page == "ホーム🏠":
    st.title("ホームページ")
    st.write("ここにホームページの内容を追加します。")

elif st.session_state.page == "ファイルアップロード📂":
    st.title("CSVファイルアップローダー")
    uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type=["csv"])
    if uploaded_file is not None:
        # アップロード結果の可視化
        df = pd.read_csv(uploaded_file)
        st.write("アップロードされたデータ:")
        st.dataframe(df)
        
        st.write("データの概要:")
        st.dataframe(df.describe())

        # データをセッションステートに保存
        st.session_state.df = df

    else:
        st.write("CSVファイルをアップロードしてください。")

elif st.session_state.page == "基礎集計📊":
    st.title("アップロードしたファイルを基礎集計します")
    if st.session_state.df is not None:
        pyg_app = StreamlitRenderer(st.session_state.df)
        pyg_app.explorer()
    else:
        st.write("CSVファイルをアップロードしてください。")