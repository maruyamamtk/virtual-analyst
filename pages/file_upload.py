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

@st.cache_data
def load_data(uploaded_file):
    df = pd.read_csv(uploaded_file)
    return df

uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type=["csv"])

if uploaded_file is not None:
    # アップロード結果の可視化
    df = load_data(uploaded_file)
    st.write("アップロードされたデータのサイズ:", df.shape)
    st.dataframe(df)

    # データをセッションステートに保存
    st.session_state.df_original = df # 生データ
    st.session_state.df = df # 分析に使用するデータ(生データを使用するケースも想定してオブジェクトを分ける)

    # カラム名を保存
    # 数値型のカラム名のリスト
    st.session_state.numeric_columns = st.session_state.df.select_dtypes(include=['number']).columns.tolist()
    # 日付型のカラム名のリスト
    st.session_state.datetime_columns = st.session_state.df.select_dtypes(include=['datetime']).columns.tolist()
    # 文字列型のカラム名のリスト
    st.session_state.non_numeric_columns = st.session_state.df.select_dtypes(exclude=['number', 'datetime']).columns.tolist()