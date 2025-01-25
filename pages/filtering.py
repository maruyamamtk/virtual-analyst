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
# フィルタリングのUIを作成
st.title("データのフィルター")
if 'df' not in st.session_state or st.session_state.df is None:
    st.write("CSVファイルをアップロードしてください。")
else:
    # 各カラムごとにフィルタを作成
    for column in st.session_state.df.columns:
        st.markdown(f"### {column}の範囲の指定")
        if st.session_state.df[column].dtype == 'object':
            unique_values = st.session_state.df[column].unique()
            # 要素数が多い場合はフィルタ条件を直接入力する
            if len(unique_values) > 10:
                user_input = st.text_input(f"{column} の値を入力してください (カンマ区切りで複数入力可)")
                if user_input:
                    selected_values = [value.strip() for value in user_input.split(',')]
                    st.session_state.df = st.session_state.df[st.session_state.df[column].isin(selected_values)]
            # 要素数が少ない場合はフィルタ条件を候補から指定する
            else:
                selected_values = st.multiselect(f"{column} の値を選択してください", unique_values, default=unique_values)
                st.session_state.df = st.session_state.df[st.session_state.df[column].isin(selected_values)]
        elif st.session_state.df[column].dtype in ['int64', 'float64']:
            min_value = st.session_state.df[column].min()
            max_value = st.session_state.df[column].max()
            selected_min_value = st.number_input(f"{column} の最小値を選択してください", min_value=min_value, max_value=max_value, value=min_value)
            selected_max_value = st.number_input(f"{column} の最大値を選択してください", min_value=min_value, max_value=max_value, value=max_value)
            st.session_state.df = st.session_state.df[(st.session_state.df[column] >= selected_min_value) &
                                                      (st.session_state.df[column] <= selected_max_value)]
        elif st.session_state.df[column].dtype == 'datetime64[ns]':
            min_date = st.date_input(f"{column} の最小日付を選択してください", st.session_state.df[column].min())
            max_date = st.date_input(f"{column} の最大日付を選択してください", st.session_state.df[column].max())
            st.session_state.df = st.session_state.df[(st.session_state.df[column] >= pd.to_datetime(min_date)) &
                                                      (st.session_state.df[column] <= pd.to_datetime(max_date))]

    # フィルタリングされたデータを表示
    st.markdown("### フィルタ状況の確認")
    st.write("フィルタリングされたデータ:")
    st.write(st.session_state.df.head())
    # 行数と列数を出力
    st.write("データの行数・列数", st.session_state.df.shape)

    # フィルタをリセットするボタン
    if st.button("フィルタをリセット"):
        st.session_state.df = st.session_state.df_original.copy()
