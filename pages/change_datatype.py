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
# データ型変換のUIを追加
st.title("データ型変換")
## dfがセッションステートに保存されていない or セッションステートに存在するが空のファイルの場合
if 'df' not in st.session_state or st.session_state.df is None:
    st.write("CSVファイルをアップロードしてください。")
else:
    st.write(":red[変換できない型を指定すると、そのカラムがnullになってしまうので注意してください]")
    st.write("その場合、ファイルの再アップロードが必要になります")
    for column in st.session_state.df.columns:
        new_type = st.selectbox(f"{column} の新しいデータ型を選択してください", 
                                options=["そのまま", "数値型", "文字列型", "日付型"], 
                                index=0)
        if new_type == "数値型":
            st.session_state.df[column] = pd.to_numeric(st.session_state.df[column], errors='coerce')
        elif new_type == "文字列型":
            st.session_state.df[column] = st.session_state.df[column].astype(str)
        elif new_type == "日付型":
            st.session_state.df[column] = pd.to_datetime(st.session_state.df[column], errors='coerce')

    st.write("変換後のデータフレーム:")
    st.write(st.session_state.df)

    # カラム名を保存
    # 数値型のカラム名のリスト
    st.session_state.numeric_columns = st.session_state.df.select_dtypes(include=['number']).columns.tolist()

    # 日付型のカラム名のリスト
    st.session_state.datetime_columns = st.session_state.df.select_dtypes(include=['datetime']).columns.tolist()

    # 数値型・日付型以外のカラム名のリスト
    st.session_state.non_numeric_columns = st.session_state.df.select_dtypes(exclude=['number', 'datetime']).columns.tolist()

    st.write("数値型のカラム:", st.session_state.numeric_columns)
    st.write("日付型のカラム:", st.session_state.datetime_columns)
    st.write("数値型・日付型以外のカラム:", st.session_state.non_numeric_columns)