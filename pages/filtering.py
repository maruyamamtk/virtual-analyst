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
    tab_list = st.tabs(
        ["フィルタ条件の設定",
         "フィルタ後のデータの確認"]
    )
    
    with tab_list[0]:
        st.markdown("## フィルタ条件の解除")
        # フィルタをリセットするボタン(目立たせるためのスタイルを追加)
        button_css = f"""
            <style>
            div.stButton > button:first-child  {{
                font-weight  : bold                ;/* 文字：太字                   */
                border       : 5px solid #ff4b4b  ;/* 枠線：赤色で5ピクセルの実線 */
                border-radius: 10px 10px 10px 10px ;/* 枠線：半径10ピクセルの角丸     */
                background   : #ff4b4b             ;/* 背景色：赤色                  */
                color        : white               ;/* 文字色：白                    */
            }}
            </style>
        """
        st.markdown(button_css, unsafe_allow_html=True)
        reset_flag = st.button("フィルタをリセット", key="reset_button")
        if reset_flag:
            # データそのものをリセット
            st.session_state.df = st.session_state.df_original.copy()
            # 対象カラムをリセット
            st.session_state.numeric_columns = st.session_state.numeric_columns_original.copy()
            st.session_state.datetime_columns = st.session_state.datetime_columns_original.copy()
            st.session_state.non_numeric_columns = st.session_state.non_numeric_columns_original.copy()

        # 使用するカラムを選択
        st.markdown("## 使用カラムの設定")
        selected_columns = st.multiselect(
            "分析に使用するカラムを選択してください",
            options=st.session_state.df_original.columns,
            default=st.session_state.df.columns
        )

        # 使用するカラムに基づいてsession_stateのデータ・カラムを更新する
        st.session_state.df = st.session_state.df[selected_columns]
        st.session_state.numeric_columns = st.session_state.df.select_dtypes(include=['number']).columns.tolist()
        st.session_state.datetime_columns = st.session_state.df.select_dtypes(include=['datetime']).columns.tolist()
        st.session_state.non_numeric_columns = st.session_state.df.select_dtypes(exclude=['number', 'datetime']).columns.tolist()

        # 各カラムごとにフィルタを作成
        st.markdown("## カラム別の範囲の指定")
        for column in st.session_state.df.columns:
            st.markdown(f"### {column}の範囲の指定")
            if st.session_state.df[column].dtype in ['object', 'string']:
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

    with tab_list[1]:
        # フィルタリングされたデータを表示
        st.markdown("## フィルタ後のデータの確認")
        st.write("フィルタリングされたデータ:")
        st.write(st.session_state.df.head())
        # 行数と列数を出力
        st.write("データの行数・列数", st.session_state.df.shape)
