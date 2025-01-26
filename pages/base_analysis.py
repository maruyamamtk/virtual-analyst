import streamlit as st
import pandas as pd
from functions.multi_pages import multi_page
import functions.func_base_analysis as fba
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
st.title("基本的な集計・グラフの描画")
## dfがセッションステートに保存されていない or セッションステートに存在するが空のファイルの場合
if 'df' not in st.session_state or st.session_state.df is None:
    st.write("CSVファイルをアップロードしてください。")
else:
    # タブの作成
    tab_list = st.tabs(
        ["データの概要",
         "1変数の統計量",
         "2変数(数値型×数値型)",
         "2変数(数値型×文字列,日付型)",
         "2変数(文字列型×文字列型)",
         "3変数"]
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
        st.markdown("### 数値型, 日付型の変数のサマリ")
        if em.coltype_error("数値型") or em.coltype_error("日付型"):
            st.write(st.session_state.df.describe(exclude="object"))

        st.markdown("### 文字列型の変数のサマリ")
        if em.coltype_error("文字列型"):
            st.write(st.session_state.df.describe(include="object"))

        # 数値型に対してはヒストグラムを描画
        st.markdown("### 特定変数の分布")
        st.markdown("#### 数値型")
        if em.coltype_error("数値型"):
            @st.fragment
            def plot_tab1_histogram():
                selected_numeric_column = st.selectbox(
                    "数値型の変数を選択してください",
                    st.session_state.numeric_columns,
                    key="numeric_column_tab1"
                )
                fig_hist = fba.histogram(st.session_state.df, selected_numeric_column)
                st.pyplot(fig_hist, clear_figure=False)
            
            plot_tab1_histogram()

        # 文字列型に対してはレコード数をカウントしたdataframeを出力
        st.markdown("#### 文字列型, 日付型")
        if em.coltype_error("文字列型") or em.coltype_error("日付型"):
            @st.fragment
            def calc_tab1_recordnum():
                selected_non_numeric_column = st.selectbox(
                    "文字列型, 日付型の変数の中から1つの変数を選択してください",
                    st.session_state.non_numeric_columns + st.session_state.datetime_columns,
                    key="non_numeric_column_tab1"
                )
                st.write(f"選択された変数: {selected_non_numeric_column}")
                df_count = fba.colname_counts(st.session_state.df, selected_non_numeric_column)
                df_count['割合'] = df_count['割合'] * 100 # 割合を0~100%に対する比率に変換
                column_config = {
                    # 割合を0~100%に対する比率で表示
                    "割合": st.column_config.ProgressColumn("レコードの比率", format="%.0f %%", min_value=0, max_value=100)
                }
                st.dataframe(df_count[[selected_non_numeric_column, 'レコード数', '割合']]
                            ,column_config=column_config)
                
            calc_tab1_recordnum()

    ##### 2変数(数値型×数値型)の統計量を出力するタブ
    with tab_list[2]:
        st.header("2変数(数値型×数値型)")
        st.divider()
        if em.coltype_error("数値型"):
            st.markdown("### 相関行列")
            @st.fragment
            def plot_tab2_heatmap():
                filtered_df = st.session_state.df[st.session_state.numeric_columns]
                fig_corr = fba.plot_correlation_heatmap(filtered_df)
                st.pyplot(fig_corr, clear_figure=False)

            plot_tab2_heatmap()

            st.markdown("### 散布図")
            @st.fragment
            def plot_tab2_scatter():
                # 散布図のパラメータを入力
                col1 = st.selectbox(
                    "1つ目の変数を選択してください",
                    st.session_state.numeric_columns,
                    key="numeric_column_tab2_0"
                )
                col2 = st.selectbox(
                    "2つ目の変数を選択してください",
                    st.session_state.numeric_columns,
                    key="numeric_column_tab2_1"
                )
                if col1 and col2:
                    fig_scatter = fba.plot_scatter(st.session_state.df, col1, col2)
                    st.pyplot(fig_scatter, clear_figure=False)

            plot_tab2_scatter()


    ##### 2変数(数値型×文字列,日付型)の統計量を出力するタブ
    with tab_list[3]:
        st.header("2変数(数値型×文字列,日付型)")
        st.divider()

        # 内部にtabを作成
        tab_list_3 = st.tabs(
            ["文字列型の場合",
            "日付型の場合"]
        )

        # 文字列型の場合の描画を実行
        with tab_list_3[0]:
            if em.coltype_error("文字列型") and em.coltype_error("数値型"):
                @st.fragment
                def plot_tab3_0_box():
                    # 描画のパラメータを入力
                    st.markdown("### 描画パラメータの設定")
                    col1 = st.selectbox(
                        "文字列型の変数を選択してください",
                        st.session_state.non_numeric_columns,
                        key="non_numeric_column_tab3_0"
                    )
                    col2 = st.selectbox(
                        "数値型の変数を選択してください",
                        st.session_state.numeric_columns,
                        key="numeric_column_tab3_0"
                    )

                    threshold = st.number_input(
                        "文字列型の変数において、特定の要素と一致するレコード数が指定割合よりも小さい場合は、**その他**に丸めて集計をします(単位: %)",
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

                    # 文字列型に対して、数値型の基礎統計量を集計
                    st.markdown(f"### {col1}カラムの要素に対する{col2}の集計")

                    # 計算処理
                    result = fba.agg_1parameter(st.session_state.df, col1, col2, threshold/100)
                    st.write(result)

                plot_tab3_0_box()

        # 日付型の場合の描画を実行
        with tab_list_3[1]:
            if em.coltype_error("日付型") and em.coltype_error("数値型"):
                @st.fragment
                def plot_tab3_1_timeline():
                    st.markdown("### 描画パラメータの設定")
                    # 描画のパラメータを入力
                    col1 = st.selectbox(
                        "日付型の変数を選択してください",
                        st.session_state.datetime_columns,
                        key="datetime_column_tab3_1"
                    )
                    col2 = st.selectbox(
                        "数値型の変数を選択してください",
                        st.session_state.numeric_columns,
                        key="numeric_column_tab3_1"
                    )
                    datetime_type = st.selectbox(
                        "集計時における日付カラムの粒度を選択してください",
                        ["月", "週", "日", "時間"],
                        key="datetime_type"
                    )
                    agg_type = st.selectbox(
                        "集計における計算方法を選択してください",
                        ["合計", "平均", "中央値", "カウント"],
                        key="agg_type"
                    )

                    # 描画の実施
                    st.markdown(f"### {datetime_type}単位での{col2}の{agg_type}の推移")
                    # 必要なデータを集計
                    agg_df = fba.agg_datetime_dataframe(st.session_state.df, datetime_type, agg_type, col1, col2)
                    plot_type = st.selectbox(
                        "描画方法を選択してください",
                        ["棒グラフ", "折れ線グラフ"],
                        key="plot_type"
                    )
                    fig_datetime_1param = fba.plot_datetime_1param(agg_df, col1, col2, plot_type, datetime_type)
                    st.pyplot(fig_datetime_1param, clear_figure=False)
                    st.markdown("### 描画に使ったデータの確認")
                    st.dataframe(agg_df)

                plot_tab3_1_timeline()


    ##### 2変数(文字列型×文字列型)の統計量を出力するタブ
    with tab_list[4]:
        st.header("2変数(文字列型×文字列型)")
        st.divider()
        if em.coltype_error("文字列型"):
            @st.fragment
            def plot_tab4_crosstab():
                st.write("各カラムにおいて、レコード数の割合が5%以下の場合は**その他**に丸め処理して集計する")
                # 描画のパラメータを入力
                col1 = st.selectbox(
                    "1つ目の変数を選択してください",
                    st.session_state.non_numeric_columns,
                    key="non_numeric_column_tab4_0"
                )
                col2 = st.selectbox(
                    "2つ目の変数を選択してください",
                    st.session_state.non_numeric_columns,
                    key="non_numeric_column_tab4_1"
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

            plot_tab4_crosstab()


    ##### 3変数の関係性を集計するタブ
    with tab_list[5]:
        st.header("3変数の集計")
        #st.write("各カラムにおいて、レコード数の割合が5%以下の場合は**その他**に丸め処理して集計する")
        st.divider()
        if em.coltype_error("数値型") and (em.coltype_error("文字列型") or em.coltype_error("日付型")):
            @st.fragment
            def plot_tab5_timeline():
                ##### 描画のパラメータを入力
                st.markdown("### 描画パラメータの設定")
                with st.expander("**数値型の変数の選択**"):
                    col_numeric = st.selectbox(
                        "集計対象の数値型の変数を選択してください",
                        st.session_state.numeric_columns,
                        key="numeric_column_tab5"
                    )
                    agg_type = st.selectbox(
                            "集計における計算方法を選択してください",
                            ["合計", "平均", "中央値", "カウント"],
                            key="agg_type_tab5"
                    )
                with st.expander("**集計時のディメンションの選択(その1)**"):
                    # ディメンション(1つ目)
                    col_dim1 = st.selectbox(
                        "1つ目のディメンション(文字列型or日付型の変数)を選択してください",
                        st.session_state.non_numeric_columns + st.session_state.datetime_columns,
                        key="non_numeric_column_tab5_1"
                    )
                    # dimの選択肢毎に前処理を実施
                    if col_dim1 in st.session_state.datetime_columns:
                        datetime_type1 = st.selectbox(
                            "集計時における日付カラムの粒度を選択してください",
                            ["月", "週", "日", "時間"],
                            key="datetime_type_tab5_1"
                        )
                    elif col_dim1 in st.session_state.non_numeric_columns:
                        threshold1 = st.number_input(
                            "文字列型の変数において、特定の要素と一致するレコード数が指定割合よりも小さい場合は、**その他**に丸めて集計をします(単位: %)",
                            min_value=0.0,
                            max_value=100.0,
                            value=5.0,
                            step=5.0,
                            key="threshold_tab5_1"
                        )
                # ディメンション(2つ目)
                with st.expander("**集計時のディメンションの選択(その2)**"):
                    col_dim2 = st.selectbox(
                        "2つ目のディメンション(文字列型or日付型の変数)を選択してください",
                        st.session_state.non_numeric_columns + st.session_state.datetime_columns,
                        key="non_numeric_column_tab5_2"
                    )
                    if col_dim1 == col_dim2:
                        st.error("ディメンションに同じカラムを指定することはできません", icon=":material/error:")
                    # dimの選択肢毎に前処理を実施
                    if col_dim2 in st.session_state.datetime_columns:
                        datetime_type2 = st.selectbox(
                            "集計時における日付カラムの粒度を選択してください",
                            ["月", "週", "日", "時間"],
                            key="datetime_type_tab5_2"
                        )
                    elif col_dim2 in st.session_state.non_numeric_columns:
                        threshold2 = st.number_input(
                            "文字列型の変数において、特定の要素と一致するレコード数が指定割合よりも小さい場合は、**その他**に丸めて集計をします(単位: %)",
                            min_value=0.0,
                            max_value=100.0,
                            value=5.0,
                            step=5.0,
                            key="threshold_tab5_2"
                        )
                if col_dim1 == col_dim2:
                    st.error("ディメンションに同じカラムを指定することはできません", icon=":material/error:")
                with st.expander("**集計方法の選択**"):
                # 集計方法を指定
                    plot_type = st.selectbox(
                            "集計方法を選択してください",
                            ["クロス集計", "時系列グラフ"],
                            key="plot_type_tab5"
                        )
                
                ##### 指定した集計方法に基づきデータ加工を行う
                # クロス集計
                if plot_type == "クロス集計" and col_dim1 != col_dim2:
                    st.header(f"{col_dim1}と{col_dim2}の属性別の、{col_numeric}の{agg_type}の変化")
                    st.write(f"行: {col_dim1}, 列: {col_dim2}")
                    st.write(f"※文字列型の変数をディメンションにした場合、レコード数の割合が一定値以下の場合は\n**その他**に丸め処理をしている")
                    # ディメンションが共に日付型データ
                    if col_dim1 in st.session_state.datetime_columns and\
                    col_dim2 in st.session_state.datetime_columns:
                        agg_df = fba.agg_datetime_2col_dataframe(st.session_state.df, datetime_type1, datetime_type2,
                                                        agg_type, col_dim1, col_dim2, col_numeric)
                        st.dataframe(agg_df)
                    # ディメンションが共に文字列型データ
                    elif col_dim1 in st.session_state.non_numeric_columns and\
                    col_dim2 in st.session_state.non_numeric_columns:
                        agg_df = fba.agg_category_2col_dataframe(st.session_state.df, col_dim1, col_dim2, col_numeric,
                                                        agg_type, threshold1, threshold2)
                        st.dataframe(agg_df)
                    # ディメンションが文字列・日付型の複合
                    else:
                        # どちらの変数が文字列なのかによって、関数の引数を変更する
                        if col_dim1 in st.session_state.non_numeric_columns:
                            col_category = col_dim1
                            threshold_input = threshold1
                            col_datetime = col_dim2
                            datetime_type_input = datetime_type2
                        else:
                            col_category = col_dim2
                            threshold_input = threshold2
                            col_datetime = col_dim1
                            datetime_type_input = datetime_type1
                        agg_df = fba.agg_category_datetime_dataframe(st.session_state.df, col_category, col_datetime, col_numeric,
                                                        agg_type, threshold_input, datetime_type_input)
                        st.dataframe(agg_df)
                # 時系列グラフ
                elif plot_type == "時系列グラフ" and col_dim1 != col_dim2:
                    st.header(f"{col_dim1}の日時経過に対する{col_numeric}の{agg_type}の推移")
                    # ディメンションが共に文字列型データの場合はエラーを返す
                    if col_dim1 in st.session_state.non_numeric_columns and\
                    col_dim2 in st.session_state.non_numeric_columns:
                        st.error("日付型のディメンションを少なくとも1つ以上選択してください", icon=":material/error:")
                    #ディメンションが共に日付型データの場合の描画
                    elif col_dim1 in st.session_state.datetime_columns and\
                    col_dim2 in st.session_state.datetime_columns:
                        # agg_dfのindex→col_dim1, column→col_dim2となる
                        agg_df = fba.agg_datetime_2col_dataframe(st.session_state.df, datetime_type1, datetime_type2,
                                                        agg_type, col_dim1, col_dim2, col_numeric)
                        fig = fba.plot_date_category_3val(agg_df, col_numeric, col_dim1, col_dim2, agg_type)
                        st.pyplot(fig, clear_figure=False)
                        st.dataframe(agg_df)
                    # ディメンションが文字列・日付型の複合
                    else:
                        # どちらの変数が文字列なのかによって、関数の引数を変更する
                        if col_dim1 in st.session_state.non_numeric_columns:
                            col_category = col_dim1
                            threshold_input = threshold1
                            col_datetime = col_dim2
                            datetime_type_input = datetime_type2
                        else:
                            col_category = col_dim2
                            threshold_input = threshold2
                            col_datetime = col_dim1
                            datetime_type_input = datetime_type1
                        agg_df = fba.agg_category_datetime_dataframe(st.session_state.df, col_category, col_datetime, col_numeric,
                                                        agg_type, threshold_input, datetime_type_input)
                        fig = fba.plot_date_category_3val(agg_df, col_numeric, col_datetime, col_category, agg_type)
                        st.pyplot(fig, clear_figure=False)
                        st.dataframe(agg_df)

            plot_tab5_timeline()
        else:
            st.write("集計に必要な変数がデータに含まれていません")