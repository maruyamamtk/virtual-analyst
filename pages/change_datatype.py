import streamlit as st
import pandas as pd
from functions.multi_pages import multi_page
import functions.error_messages as em

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
# dfが存在する場合は型変換を実行
else:
    st.write(":red[変換できない型を指定すると、そのカラムがnullになってしまうので注意してください]")
    st.write("その場合、ファイルの再アップロードが必要になります")
    for column in st.session_state.df.columns:
        new_type = st.selectbox(f"{column} の新しいデータ型を選択してください(現状の型: {st.session_state.df[column].dtypes})", 
                                options=["そのまま", "数値型", "文字列型", "日付型"], 
                                index=0)
        # filter機能をリセットした際にカラムの型が元に戻らないように、df_originalも変換する
        if new_type == "数値型":
            st.session_state.df[column] = pd.to_numeric(st.session_state.df[column], errors='coerce')
            st.session_state.df_original[column] = pd.to_numeric(st.session_state.df_original[column], errors='coerce')
        elif new_type == "文字列型":
            st.session_state.df[column] = st.session_state.df[column].astype(str)
            st.session_state.df_original[column] = st.session_state.df_original[column].astype(str)
        elif new_type == "日付型":
            st.session_state.df[column] = pd.to_datetime(st.session_state.df[column], errors='coerce')
            st.session_state.df_original[column] = pd.to_datetime(st.session_state.df_original[column], errors='coerce')

    # 不適切な変換についてはアラートを出す
    em.all_null_warning("数値型")
    em.all_null_warning("文字列型")
    em.all_null_warning("日付型")

    st.write("変換後のデータフレーム:")
    st.write(st.session_state.df)

    # カラム名を保存
    # 数値型のカラム名のリスト
    st.session_state.numeric_columns = st.session_state.df.select_dtypes(include=['number']).columns.tolist()
    # 日付型のカラム名のリスト
    st.session_state.datetime_columns = st.session_state.df.select_dtypes(include=['datetime']).columns.tolist()
    # 文字列型のカラム名のリスト
    st.session_state.non_numeric_columns = st.session_state.df.select_dtypes(exclude=['number', 'datetime']).columns.tolist()

    st.write("数値型のカラム:", st.session_state.numeric_columns)
    st.write("日付型のカラム:", st.session_state.datetime_columns)
    st.write("文字列型のカラム:", st.session_state.non_numeric_columns)