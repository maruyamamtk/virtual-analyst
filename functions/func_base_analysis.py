import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import japanize_matplotlib
import functions.download_files as download_files
from datetime import datetime

##### 1変数の分布の可視化
# 数値型のヒストグラム
def histogram(df, colname):
    fig, ax = plt.subplots()
    sns.histplot(df[colname], kde=True, ax=ax)
    ax.set_title(f'ヒストグラム: {colname}')
    ax.set_xlabel(colname)
    ax.set_ylabel('頻度')
    # ファイルダウンロード
    download_files.download_file(fig, colname + 'のヒストグラム', key="histogram")
    return fig

# 文字列型の度数分布表
def colname_counts(df, colname, download_flag=False, threshold=0.05):
    # 項目ごとに要素の数を数える
    counts = df[colname].value_counts().reset_index()
    counts.columns = [colname, 'レコード数']
    
    # レコード数の全体に対する割合を計算
    counts['割合'] = counts['レコード数'] / counts['レコード数'].sum()
    # レコード数を降順に並べ替え
    counts = counts.sort_values(by='レコード数', ascending=False).reset_index(drop=True)
    # 割合が閾値以下の場合に「その他」というカテゴリを与える
    counts['カテゴリ'] = counts.apply(lambda row: 'その他' if row['割合'] <= threshold else row[colname], axis=1)
    
    # ファイルダウンロードを行うかどうか判定
    # 別の描画関数の内部で呼び出されることがあるため、flagによる分岐を設定
    if download_flag:
        # 現在時刻を取得
        now = datetime.now()
        # 文字列にフォーマット
        current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        download_files.download_file(counts, colname + 'の度数分布', key="colname_counts"+current_time_str)
    return counts

##### 2変数の分布の可視化
# 相関行列のヒートマップ
def plot_correlation_heatmap(df):
    corr = df.corr()
    fig, ax = plt.subplots()
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
    ax.set_title('相関行列のヒートマップ')
    # ファイルダウンロード
    download_files.download_file(fig, "相関行列", key="plot_correlation_heatmap")
    return fig

# 数値型×数値型
def plot_scatter(df, col1, col2):
    fig, ax = plt.subplots()
    sns.scatterplot(x=df[col1], y=df[col2], ax=ax)
    ax.set_title(f'{col1}と{col2}の散布図')
    ax.set_xlabel(col1)
    ax.set_ylabel(col2)
    # ファイルダウンロード
    download_files.download_file(fig, col1+"と"+col2+"の散布図", key="plot_scatter")
    return fig

# 数値型×文字列型
def plot_box(df, col1, col2, threshold):
    # 数値型の度数分布を集計しておく
    value_counts = colname_counts(df, col1, False, threshold)
    # 度数分布の割合を基に算出したカテゴリをleft join
    df = pd.merge(df, value_counts[[col1, 'カテゴリ']], on=col1, how="left")

    fig, ax = plt.subplots()
    sns.boxplot(x=df["カテゴリ"], y=df[col2], ax=ax)
    #ax.set_title(f'{col1}に対する{col2}の箱ひげ図')
    ax.set_xlabel(col1)
    ax.set_ylabel(col2)
    # ファイルダウンロード
    download_files.download_file(fig, col1+"に対する"+col2+"の分布の比較",
                                 key="plot_box")
    return fig

# 1つの文字列型ごとに数値の集計を行う
def agg_1parameter(df, col1, col2, threshold):
    # 数値型の度数分布を集計しておく
    value_counts = colname_counts(df, col1, False, threshold)
    # 度数分布の割合を基に算出したカテゴリをleft join
    df = pd.merge(df, value_counts[[col1, 'カテゴリ']], on=col1, how="left")

    # 指定された集計を実施
    agg_data_list = [] # 変数の初期化
    agg_data = df[['カテゴリ']].drop_duplicates()
    # 集計値をリストに追加
    agg_data_list.append(df.groupby(['カテゴリ'])[col2].count().reset_index().rename(columns={col2:'レコード数'}))
    agg_data_list.append(df.groupby(['カテゴリ'])[col2].sum().reset_index().rename(columns={col2:'合計'}))
    agg_data_list.append(df.groupby(['カテゴリ'])[col2].mean().reset_index().rename(columns={col2:'平均値'}))
    agg_data_list.append(df.groupby(['カテゴリ'])[col2].median().reset_index().rename(columns={col2:'中央値'}))
    agg_data_list.append(df.groupby(['カテゴリ'])[col2].max().reset_index().rename(columns={col2:'最大値'}))
    agg_data_list.append(df.groupby(['カテゴリ'])[col2].min().reset_index().rename(columns={col2:'最小値'}))
    # 集計値を１つのテーブルに集約
    for df_tmp in agg_data_list:
        agg_data = pd.merge(agg_data, df_tmp, on='カテゴリ', how='left')

    # 元のカラム名に戻してソートする
    agg_data = agg_data.rename(columns = {'カテゴリ': col1})
    agg_data = agg_data[~agg_data[col1].isnull()]
    agg_data = agg_data.sort_values(by='レコード数', ascending=False)

    # ファイルダウンロード
    download_files.download_file(agg_data, col1+"に対する"+col2+"の集計値",
                                 key="agg_1parameter")
    return agg_data

# 時系列の変数を用いて数値を集計する
def agg_datetime_dataframe(df_input, datetime_type, agg_type, col_datetime, col_numeric):
    df = df_input[[col_datetime, col_numeric]].copy() # 必要カラムのみに絞りこみ
    df.set_index(col_datetime, inplace=True)

    # datetime_typeに応じて日付カラムの粒度を変更し、agg_typeに基づいて集計
    if datetime_type == '月':
        if agg_type == '合計':
            agg_df = df.resample('M').sum()
        elif agg_type == '平均':
            agg_df = df.resample('M').mean()
        elif agg_type == '中央値':
            agg_df = df.resample('M').median()
        elif agg_type == 'カウント':
            agg_df = df.resample('M').count()
    elif datetime_type == '週':
        if agg_type == '合計':
            agg_df = df.resample('W').sum()
        elif agg_type == '平均':
            agg_df = df.resample('W').mean()
        elif agg_type == '中央値':
            agg_df = df.resample('W').median()
        elif agg_type == 'カウント':
            agg_df = df.resample('W').count()
    elif datetime_type == '日':
        if agg_type == '合計':
            agg_df = df.resample('D').sum()
        elif agg_type == '平均':
            agg_df = df.resample('D').mean()
        elif agg_type == '中央値':
            agg_df = df.resample('D').median()
        elif agg_type == 'カウント':
            agg_df = df.resample('D').count()
    elif datetime_type == '時間':
        if agg_type == '合計':
            agg_df = df.resample('H').sum()
        elif agg_type == '平均':
            agg_df = df.resample('H').mean()
        elif agg_type == '中央値':
            agg_df = df.resample('H').median()
        elif agg_type == 'カウント':
            agg_df = df.resample('H').count()

    return agg_df.reset_index().sort_values(by=col_datetime, ascending=True)

# 時系列に対する1変数の推移の描画
def plot_datetime_1param(df, col_datetime, col_numeric, plot_type, datetime_type):
    # datetime_typeに応じてdf[col_datetime]のデータの中身を変更
    if datetime_type == '日'  or datetime_type == '週':
        df[col_datetime] = df[col_datetime].dt.strftime('%Y-%m-%d')
    elif datetime_type == '月':
        df[col_datetime] = df[col_datetime].dt.strftime('%Y-%m')
    elif datetime_type == '時間':
        df[col_datetime] = df[col_datetime].dt.strftime('%m-%d %H')

    fig, ax = plt.subplots()
    # plot_typeに応じてグラフを描き分ける
    if plot_type == '棒グラフ':
        df.plot(kind='bar', x=col_datetime, y=col_numeric, ax=ax)
    elif plot_type == '折れ線グラフ':
        df.plot(kind='line', x=col_datetime, y=col_numeric, ax=ax)
    else:
        raise ValueError("plot_typeは'棒グラフ'または'折れ線グラフ'のいずれかである必要があります。")

    ax.set_title(f'{col_datetime}に対する{col_numeric}の{plot_type}')
    ax.set_xlabel(col_datetime)
    ax.set_ylabel(col_numeric + "の集計値")
    plt.xticks(rotation=45)
    plt.tight_layout()

    # ファイルダウンロード
    download_files.download_file(fig, col_datetime+"に対する"+col_numeric+"の推移",
                                 key="plot_datetime_1param")

    return fig

# 文字列型×文字列型
# ベースとなるクロス集計表を作成
def cross_counts(df_input, col1, col2, threshold=0.05):
    # st.session_state.dfに直接影響が出ないようコピーを作成
    df = df_input.copy()
    
    # col1, col2に対して「その他」というカテゴリを与える(度数分布がthreshold以下)
    counts_col1 = colname_counts(df, col1, False, threshold)
    df['カテゴリ1'] = df[col1].map(counts_col1.set_index(col1)['カテゴリ'])
    counts_col2 = colname_counts(df, col2, False, threshold)
    df['カテゴリ2'] = df[col2].map(counts_col2.set_index(col2)['カテゴリ'])
    
    # クロス集計を行う
    cross_tab = pd.crosstab(df['カテゴリ1'], df['カテゴリ2'])  
    # 各カテゴリの要素数を計算
    counts = cross_tab.stack().reset_index()
    counts.columns = ['カテゴリ1', 'カテゴリ2', '要素数']
     
    # ピボットテーブルを作成
    pivot_table = counts.pivot(index='カテゴリ1', columns='カテゴリ2', values='要素数')

    return pivot_table
    
# heatmapの作成
def plot_cross_heatmap(df, col1, col2):
    # クロス集計表を出力
    pivot_table = cross_counts(df, col1, col2)

    # ヒートマップを作成
    fig, ax = plt.subplots()
    sns.heatmap(pivot_table, annot=True, fmt="d", cmap="coolwarm", ax=ax)
    ax.set_title(f'{col1}と{col2}のクロス集計ヒートマップ')

    # ファイルダウンロード
    download_files.download_file(fig, col1+"と"+col2+"に対するレコード数の分布",
                                 key="plot_cross_heatmap")
    return fig

# 積み上げ棒グラフの作成
def plot_cross_bar(df, col1, col2, normalize):
    # クロス集計表を出力
    pivot_table = cross_counts(df, col1, col2)
    # normalizeを行う場合は、割合が算出されるように書き換える
    if normalize:
        pivot_table = pivot_table.div(pivot_table.sum(axis=1), axis=0)

    # 積み上げ棒グラフを作成
    fig, ax = plt.subplots()
    # 積み上げ棒グラフを描画
    pivot_table.plot(kind='bar', stacked=True, ax=ax)
    
    ax.set_title(f'{col1}と{col2}の積み上げ棒グラフ')
    ax.set_xlabel(col1)
    ax.set_ylabel('割合' if normalize else '要素数')
    ax.legend(title=col2)
    # ファイルダウンロード
    download_files.download_file(fig, f'{col1}と{col2}の積み上げ棒グラフ',
                                 key="plot_cross_bar")
    
    return fig

# 3変数の集計
# 日付×日付ごとにクロス集計
def agg_datetime_2col_dataframe(df_input, datetime_type1, datetime_type2,
                                agg_type, col_datetime1, col_datetime2, col_numeric):
    df = df_input[[col_datetime1, col_datetime2, col_numeric]].copy()  # 必要カラムのみに絞りこみ

    # datetime_type1に応じて日付カラムの粒度を変更
    if datetime_type1 == '日':
        df[col_datetime1] = df[col_datetime1].dt.date
    elif datetime_type1 == '月':
        df[col_datetime1] = df[col_datetime1].dt.to_period('M').dt.to_timestamp()
    elif datetime_type1 == '週':
        df[col_datetime1] = df[col_datetime1].dt.to_period('W').dt.to_timestamp()
    elif datetime_type1 == '時間':
        df[col_datetime1] = df[col_datetime1].dt.floor('H')
    # datetime_type2に応じて日付カラムの粒度を変更
    if datetime_type2 == '日':
        df[col_datetime2] = df[col_datetime2].dt.date
    elif datetime_type2 == '月':
        df[col_datetime2] = df[col_datetime2].dt.to_period('M').dt.to_timestamp()
    elif datetime_type2 == '週':
        df[col_datetime2] = df[col_datetime2].dt.to_period('W').dt.to_timestamp()
    elif datetime_type2 == '時間':
        df[col_datetime2] = df[col_datetime2].dt.floor('H')

    # 集計
    if agg_type == '合計':
        agg_df = df.groupby([col_datetime1, col_datetime2])[col_numeric].sum().reset_index()
    elif agg_type == '平均':
        agg_df = df.groupby([col_datetime1, col_datetime2])[col_numeric].mean().reset_index()
    elif agg_type == '中央値':
        agg_df = df.groupby([col_datetime1, col_datetime2])[col_numeric].median().reset_index()
    elif agg_type == 'カウント':
        agg_df = df.groupby([col_datetime1, col_datetime2])[col_numeric].count().reset_index()

    # datetime_type1に応じてdf[col_datetime]のデータの中身を変更
    if datetime_type1 == '日'  or datetime_type1 == '週':
        agg_df[col_datetime1] = agg_df[col_datetime1].dt.strftime('%Y-%m-%d')
    elif datetime_type1 == '月':
        agg_df[col_datetime1] = agg_df[col_datetime1].dt.strftime('%Y-%m')
    elif datetime_type1 == '時間':
        agg_df[col_datetime1] = agg_df[col_datetime1].dt.strftime('%m-%d %H')
    # datetime_type2に応じてdf[col_datetime]のデータの中身を変更
    if datetime_type2 == '日'  or datetime_type2 == '週':
        agg_df[col_datetime2] = agg_df[col_datetime2].dt.strftime('%Y-%m-%d')
    elif datetime_type2 == '月':
        agg_df[col_datetime2] = agg_df[col_datetime2].dt.strftime('%Y-%m')
    elif datetime_type2 == '時間':
        agg_df[col_datetime2] = agg_df[col_datetime2].dt.strftime('%m-%d %H')

    # アウトプット用にデータを整形
    agg_df = agg_df.sort_values(by=[col_datetime1, col_datetime2], ascending=True)
    agg_df = pd.pivot(agg_df, index=col_datetime1, columns=col_datetime2, values=col_numeric)
    # ファイルダウンロード
    download_files.download_file(agg_df, f'{col_datetime1},{col_datetime2}に対する{col_numeric}のクロス集計',
                                 key="agg_category_datetime_dataframe", index_flag=True)
    return agg_df

# 文字列型×文字列型ごとにクロス集計
def agg_category_2col_dataframe(df_input, col1, col2, col_numeric, agg_type, threshold1=0.05, threshold2=0.05):
    # st.session_state.dfに直接影響が出ないようコピーを作成
    df = df_input.copy()
    
    # col1, col2に対して「その他」というカテゴリを与える(度数分布がthreshold以下)
    counts_col1 = colname_counts(df, col1, False, threshold1)
    df['カテゴリ1'] = df[col1].map(counts_col1.set_index(col1)['カテゴリ'])
    counts_col2 = colname_counts(df, col2, False, threshold1)
    df['カテゴリ2'] = df[col2].map(counts_col2.set_index(col2)['カテゴリ'])

    # 必要なカラムだけ抽出
    df = df[['カテゴリ1', 'カテゴリ2', col_numeric]]
    # agg_typeに応じて集計を実施
    if agg_type == '合計':
        agg_df = df.groupby(['カテゴリ1', 'カテゴリ2'])[col_numeric].sum().reset_index()
    elif agg_type == '平均':
        agg_df = df.groupby(['カテゴリ1', 'カテゴリ2'])[col_numeric].mean().reset_index()
    elif agg_type == '中央値':
        agg_df = df.groupby(['カテゴリ1', 'カテゴリ2'])[col_numeric].median().reset_index()
    elif agg_type == 'カウント':
        agg_df = df.groupby(['カテゴリ1', 'カテゴリ2'])[col_numeric].count().reset_index()

    agg_df = agg_df.sort_values(by=['カテゴリ1', 'カテゴリ2'], ascending=True)
    agg_df = pd.pivot(agg_df, index='カテゴリ1', columns='カテゴリ2', values=col_numeric)
    # ファイルダウンロード
    download_files.download_file(agg_df, f'{col1},{col2}に対する{col_numeric}のクロス集計',
                                 key="agg_category_datetime_dataframe", index_flag=True)
    return agg_df

# 文字列型×日付型ごとにクロス集計
def agg_category_datetime_dataframe(df_input, col_category, col_datetime, col_numeric,
                                                        agg_type, threshold_input, datetime_type_input):
    # st.session_state.dfに直接影響が出ないようコピーを作成
    df = df_input.copy()

    # col_categoryに対して「その他」というカテゴリを与える(度数分布がthreshold_input以下)
    counts_col1 = colname_counts(df, col_category, False, threshold_input)
    df['カテゴリ'] = df[col_category].map(counts_col1.set_index(col_category)['カテゴリ'])

    # datetime_type_inputに応じて日付カラムの粒度を変更
    if datetime_type_input == '日':
        df[col_datetime] = df[col_datetime].dt.date
    elif datetime_type_input == '月':
        df[col_datetime] = df[col_datetime].dt.to_period('M').dt.to_timestamp()
    elif datetime_type_input == '週':
        df[col_datetime] = df[col_datetime].dt.to_period('W').dt.to_timestamp()
    elif datetime_type_input == '時間':
        df[col_datetime] = df[col_datetime].dt.floor('H')

    # 集計
    if agg_type == '合計':
        agg_df = df.groupby([col_datetime, 'カテゴリ'])[col_numeric].sum().reset_index()
    elif agg_type == '平均':
        agg_df = df.groupby([col_datetime, 'カテゴリ'])[col_numeric].mean().reset_index()
    elif agg_type == '中央値':
        agg_df = df.groupby([col_datetime, 'カテゴリ'])[col_numeric].median().reset_index()
    elif agg_type == 'カウント':
        agg_df = df.groupby([col_datetime, 'カテゴリ'])[col_numeric].count().reset_index()
    
    # datetime_type_inputに応じてdf[col_datetime]のデータの中身を変更
    if datetime_type_input == '日'  or datetime_type_input == '週':
        agg_df[col_datetime] = agg_df[col_datetime].dt.strftime('%Y-%m-%d')
    elif datetime_type_input == '月':
        agg_df[col_datetime] = agg_df[col_datetime].dt.strftime('%Y-%m')
    elif datetime_type_input == '時間':
        agg_df[col_datetime] = agg_df[col_datetime].dt.strftime('%m-%d %H')

    agg_df = agg_df.sort_values(by=[col_datetime, 'カテゴリ'], ascending=True)
    agg_df = pd.pivot(agg_df, index=col_datetime, columns='カテゴリ', values=col_numeric)

    # ファイルダウンロード
    download_files.download_file(agg_df, f'{col_datetime},{col_category}に対する{col_numeric}のクロス集計',
                                 key="agg_category_datetime_dataframe", index_flag=True)
    return agg_df

# 3変数を用いた時系列プロット
def plot_date_category_3val(df, col_numeric, col_timeline, col_category,
                            agg_type, plot_type, plot_agg_type1, plot_agg_type2):
    # 欠損値は0を補完する
    df = df.fillna(0)

    # 割合で描画するかどうかで、データ & ラベルを変更する
    if plot_agg_type1:
        df = df.div(df.sum(axis=1), axis=0) * 100
        ylabel = f'{col_numeric}の割合 (%)'
    else:
        ylabel = col_numeric

    fig, ax = plt.subplots()

    if plot_type == '棒グラフ':
        if plot_agg_type2:
            # 積み上げ棒グラフ
            df.plot(kind='bar', stacked=True, ax=ax)
        else:
            # 通常の棒グラフ
            df.plot(kind='bar', ax=ax)
    elif plot_type == '折れ線グラフ':
        # 折れ線グラフ
        for category in df.columns:
            ax.plot(df.index, df[category], label=category)

    ax.set_title(f'日付に対する{col_category}毎の{col_numeric}の{agg_type}の推移')
    ax.set_xlabel(col_timeline)
    ax.set_ylabel(ylabel)

    # 凡例をグラフの枠の外側（右側）に配置
    ax.legend(title=col_category, bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # ファイルダウンロード
    download_files.download_file(fig, f'{col_timeline}に対する{col_category}毎の{col_numeric}の推移',
                                 key="plot_date_category_3val")

    return fig