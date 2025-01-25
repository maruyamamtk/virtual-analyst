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
if 'df' not in st.session_state or st.session_state.df is None:
    st.write("CSVファイルをアップロードしてください。")
else:
    # フィルタリングのUIを作成
    st.title("データフィルタリング")

    # 各カラムごとにフィルタを作成
    for column in st.session_state.df.columns:
        if st.session_state.df[column].dtype == 'object':
            unique_values = st.session_state.df[column].unique()
            selected_values = st.multiselect(f"{column} の値を選択してください", unique_values, default=unique_values)
            st.session_state.df = st.session_state.df[st.session_state.df[column].isin(selected_values)]
        elif st.session_state.df[column].dtype in ['int64', 'float64']:
            min_value = st.session_state.df[column].min()
            max_value = st.session_state.df[column].max()
            selected_range = st.slider(f"{column} の範囲を選択してください", min_value, max_value, (min_value, max_value))
            st.session_state.df = st.session_state.df[(st.session_state.df[column] >= selected_range[0]) & (st.session_state.df[column] <= selected_range[1])]
        elif st.session_state.df[column].dtype == 'datetime64[ns]':
            min_date = st.session_state.df[column].min()
            max_date = st.session_state.df[column].max()
            selected_date_range = st.date_input(f"{column} の範囲を選択してください", [min_date, max_date])
            st.session_state.df = st.session_state.df[(st.session_state.df[column] >= pd.to_datetime(selected_date_range[0])) & (st.session_state.df[column] <= pd.to_datetime(selected_date_range[1]))]

    # フィルタリングされたデータを表示
    st.write("フィルタリングされたデータ:")
    st.write(st.session_state.df)

    # フィルタをリセットするボタン
    if st.button("フィルタをリセット"):
        st.session_state.df = st.session_state.df_original.copy()
        st.experimental_rerun()
