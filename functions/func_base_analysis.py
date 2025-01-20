import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import japanize_matplotlib

##### 1変数の分布の可視化
# 量的変数のヒストグラム
def histogram(df, colname):
    fig, ax = plt.subplots()
    sns.histplot(df[colname], kde=True, ax=ax)
    ax.set_title(f'ヒストグラム: {colname}')
    ax.set_xlabel(colname)
    ax.set_ylabel('頻度')
    return fig

# 質的変数の度数分布表
def colname_counts(df, colname, threshold=0.05):
    # 項目ごとに要素の数を数える
    counts = df[colname].value_counts().reset_index()
    counts.columns = [colname, 'レコード数']
    
    # レコード数の全体に対する割合を計算
    counts['割合'] = counts['レコード数'] / counts['レコード数'].sum()
    # レコード数を降順に並べ替え
    counts = counts.sort_values(by='レコード数', ascending=False).reset_index(drop=True)
    # 割合が閾値以下の場合に「その他」というカテゴリを与える
    counts['カテゴリ'] = counts.apply(lambda row: 'その他' if row['割合'] <= threshold else row[colname], axis=1)
    
    return counts

##### 2変数の分布の可視化
# 相関行列のヒートマップ
def plot_correlation_heatmap(df):
    corr = df.corr()
    fig, ax = plt.subplots()
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
    ax.set_title('相関行列のヒートマップ')
    return fig

# 量的変数×量的変数
def plot_scatter(df, col1, col2):
    fig, ax = plt.subplots()
    sns.scatterplot(x=df[col1], y=df[col2], ax=ax)
    ax.set_title(f'{col1}と{col2}の散布図')
    ax.set_xlabel(col1)
    ax.set_ylabel(col2)
    return fig

# 量的変数×質的変数
def plot_box(df, col1, col2, threshold):
    # 量的変数の度数分布を集計しておく
    value_counts = colname_counts(df, col1, threshold)
    # 度数分布の割合を基に算出したカテゴリをleft join
    df = pd.merge(df, value_counts[[col1, 'カテゴリ']], on=col1, how="left")

    fig, ax = plt.subplots()
    sns.boxplot(x=df["カテゴリ"], y=df[col2], ax=ax)
    #ax.set_title(f'{col1}に対する{col2}の箱ひげ図')
    ax.set_xlabel(col1)
    ax.set_ylabel(col2)
    return fig

# 1つの質的変数ごとに数値の集計を行う
def agg_1parameter(df, col1, col2, threshold, operation):
    # 量的変数の度数分布を集計しておく
    value_counts = colname_counts(df, col1, threshold)
    # 度数分布の割合を基に算出したカテゴリをleft join
    df = pd.merge(df, value_counts[[col1, 'カテゴリ']], on=col1, how="left")

    # operagionごとに指定された集計を実施
    agg_data = None # 変数の初期化
    if operation == "合計":
        agg_data = df.groupby(['カテゴリ'])[col2].sum().reset_index()
    elif operation == "平均":
        agg_data = df.groupby(['カテゴリ'])[col2].mean().reset_index()
    elif operation == "中央値":
        agg_data = df.groupby(['カテゴリ'])[col2].median().reset_index()
    elif operation == "最大値":
        agg_data = df.groupby(['カテゴリ'])[col2].max().reset_index()
    elif operation == "最小値":
        agg_data = df.groupby(['カテゴリ'])[col2].min().reset_index()

    # 元のカラム名に戻す
    agg_data = agg_data.rename(columns = {'カテゴリ': col1})
    
    return agg_data.sort_values(by=col2, ascending=False)

# 質的変数×質的変数
# ベースとなるクロス集計表を作成
def cross_counts(df_input, col1, col2, threshold=0.05):
    # st.session_state.dfに直接影響が出ないようコピーを作成
    df = df_input.copy()
    
    # col1, col2に対して「その他」というカテゴリを与える(度数分布がthreshold以下)
    counts_col1 = colname_counts(df, col1, threshold)
    df['カテゴリ1'] = df[col1].map(counts_col1.set_index(col1)['カテゴリ'])
    counts_col2 = colname_counts(df, col2, threshold)
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
    
    return fig