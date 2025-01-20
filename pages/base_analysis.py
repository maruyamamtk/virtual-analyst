import streamlit as st
import pandas as pd
from functions.multi_pages import multi_page
import functions.func_base_analysis as fba

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
st.title("基本的な集計・グラフの描画")
## dfがセッションステートに保存されていない or セッションステートに存在するが空のファイルの場合
if 'df' not in st.session_state or st.session_state.df is None:
    st.write("CSVファイルをアップロードしてください。")
else:
    # タブの作成
    tab_list = st.tabs(
        ["データの概要",
         "1変数の統計量",
         "2変数(量的変数×量的変数)",
         "2変数(量的変数×質的変数)",
         "2変数(質的変数×質的変数)"]
        )

    ##### データの概要を出力するタブ
    with tab_list[0]:
        col_left, col_right = st.columns([0.3, 0.7], gap = 'small', vertical_alignment = 'top')
        with col_left:
            st.header("基本情報")
            st.divider()
            # 行数と列数を出力
            st.write("データの行数・列数", st.session_state.df.shape)
            # 型と欠損値を直接取得
            df_tmp_1 = st.session_state.df.dtypes
            df_tmp_1.columns = ['カラム名', 'データ型']
            df_tmp_2 = st.session_state.df.isnull().sum()
            df_tmp_2.columns = ['カラム名', '欠損レコード数']
            df_summary = pd.concat([df_tmp_1, df_tmp_2], axis=1)
            # 出力用にデータを加工
            column_config = {
                # 割合を0~100%に対する比率で表示
                "": st.column_config.TextColumn("カラム名"),
                "0": st.column_config.TextColumn("データ型"),
                "1": st.column_config.NumberColumn("欠損レコード数"),
            }
            st.dataframe(df_summary, column_config=column_config)
        with col_right:
            st.header("データの概要")
            st.divider()
            st.markdown("冒頭の5行")
            st.write(st.session_state.df.head())
            st.markdown("末尾の5行")
            st.write(st.session_state.df.tail())

    ##### 1変数の統計量を出力するタブ
    with tab_list[1]:
        st.header("1変数の統計量")
        st.divider()
        # describe関数の実行結果を出力
        st.markdown("### 量的変数のサマリ")
        st.write(st.session_state.df.describe())

        st.markdown("### 質的変数のサマリ")
        st.write(st.session_state.df.describe(exclude="number"))

        # 量的変数に対してはヒストグラムを描画
        st.markdown("### 特定変数の分布")
        st.markdown("#### 量的変数")
        selected_numeric_column = st.selectbox(
            "量的変数を選択してください",
            st.session_state.numeric_columns,
            key="numeric_column1"
        )
        fig_hist = fba.histogram(st.session_state.df, selected_numeric_column)
        st.pyplot(fig_hist, clear_figure=False)

        # 質的変数に対してはレコード数をカウントしたdataframeを出力
        st.markdown("#### 質的変数")
        selected_non_numeric_column = st.selectbox(
            "質的変数を選択してください",
            st.session_state.non_numeric_columns,
            key="non_numeric_column1"
        )
        st.write(f"選択された質的変数: {selected_non_numeric_column}")
        df_count = fba.colname_counts(st.session_state.df, selected_non_numeric_column)
        df_count['割合'] = df_count['割合'] * 100 # 割合を0~100%に対する比率に変換
        column_config = {
            # 割合を0~100%に対する比率で表示
            "割合": st.column_config.ProgressColumn("レコードの比率", format="%.0f %%", min_value=0, max_value=100)
        }
        st.dataframe(df_count[[selected_non_numeric_column, 'レコード数', '割合']]
                     ,column_config=column_config)

    ##### 2変数(量的変数×量的変数)の統計量を出力するタブ
    with tab_list[2]:
        st.header("2変数(量的変数×量的変数)")
        st.divider()
        st.markdown("### 相関行列")
        filtered_df = st.session_state.df[st.session_state.numeric_columns]
        fig_corr = fba.plot_correlation_heatmap(filtered_df)
        st.pyplot(fig_corr, clear_figure=False)

        st.markdown("### 散布図")
        # 散布図のパラメータを入力
        col1 = st.selectbox(
            "1つ目の量的変数を選択してください",
            st.session_state.numeric_columns,
            key="numeric_column2"
        )
        col2 = st.selectbox(
            "2つ目の量的変数を選択してください",
            st.session_state.numeric_columns,
            key="numeric_column3"
        )
        if col1 and col2:
            fig_scatter = fba.plot_scatter(st.session_state.df, col1, col2)
            st.pyplot(fig_scatter, clear_figure=False)


    ##### 2変数(量的変数×質的変数)の統計量を出力するタブ
    with tab_list[3]:
        st.header("2変数(量的変数×質的変数)")
        st.divider()
        # 描画のパラメータを入力
        st.markdown("### 描画パラメータの設定")
        col1 = st.selectbox(
            "質的変数を選択してください",
            st.session_state.non_numeric_columns,
            key="non_numeric_column2"
        )
        col2 = st.selectbox(
            "量的変数を選択してください",
            st.session_state.numeric_columns,
            key="numeric_column4"
        )
        threshold = st.number_input(
            "質的変数において、特定の要素と一致するレコード数が指定割合よりも小さい場合は、**その他**に丸めて集計をします(単位: %)",
            min_value=0.0,
            max_value=100.0,
            value=5.0,
            step=5.0,
            key="threshold2"
        )
        # 度数分布を丸めた状況と、それに対する箱ひげを同時に描画
        st.markdown(f"### {col1}カラムの要素に対する{col2}の分布の比較")
        col_left, col_right = st.columns([0.4, 0.6], gap = 'small', vertical_alignment = 'top')
        # 度数分布の表示
        with col_left:
            st.markdown("#### カラムの要素とレコード数の関係")
            st.write(f"レコード数の割合が{threshold:.0f}%以下の場合は\n**その他**に丸め処理")
            df_tmp = fba.colname_counts(st.session_state.df, col1)
            df_category = df_tmp[['カテゴリ', 'レコード数', '割合']].groupby('カテゴリ').sum().sort_values(by='レコード数', ascending=False)
            
            # 表示用にデータを加工
            df_category["割合"] = df_category["割合"]*100
            column_config = {
                # 割合を0~100%に対する比率で表示
                "カテゴリ": st.column_config.TextColumn("カラムの値"),
                "割合": st.column_config.ProgressColumn("レコードの比率", format="%.0f %%", min_value=0, max_value=100)
            }
            st.write(f"**{col1}カラムの要素とレコード数の関係**")
            st.dataframe(df_category, column_config=column_config)
        # 箱ひげ図の描画
        with col_right:   
            if col1 and col2:
                st.markdown("#### 箱ひげ図による分布の比較")
                fig_box = fba.plot_box(st.session_state.df, col1, col2, threshold/100)
                st.pyplot(fig_box, clear_figure=False)

        # 質的変数に対して、量的変数の基礎統計量を集計
        st.markdown(f"### {col1}カラムの要素に対する{col2}の集計")

        # 計算処理
        result = fba.agg_1parameter(st.session_state.df, col1, col2, threshold/100)
        st.write(result)

    ##### 2変数(質的変数×質的変数)の統計量を出力するタブ
    with tab_list[4]:
        st.header("2変数(質的変数×質的変数)")
        st.divider()
        st.write("各カラムにおいて、レコード数の割合が5%以下の場合は**その他**に丸め処理して集計する")
        # 描画のパラメータを入力
        col1 = st.selectbox(
            "質的変数を選択してください",
            st.session_state.non_numeric_columns,
            key="non_numeric_column3"
        )
        col2 = st.selectbox(
            "質的変数を選択してください",
            st.session_state.non_numeric_columns,
            key="non_numeric_column4"
        )

        if col1 and col2:
            # ヒートマップを描画
            st.markdown("### 2カラム選定時のクロス集計表")
            fig_cross_heatmap = fba.plot_cross_heatmap(st.session_state.df, col1, col2)
            st.pyplot(fig_cross_heatmap, clear_figure=False)
            # 積み上げ棒グラフを描画
            st.markdown("### 2カラム選定時の積み上げ棒グラフ")
            normalize = st.checkbox('実数ではなく割合で描画する', value=False)
            fig_cross_bar = fba.plot_cross_bar(st.session_state.df, col1, col2, normalize)
            st.pyplot(fig_cross_bar, clear_figure=False)