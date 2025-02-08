import streamlit as st
from functions.multi_pages import multi_page
from functions.func_chatbot import use_secret
 
# 環境変数が設定されていない場合、以下のコマンドを実行する必要がある
# python -m streamlit run .\streamlit_app.py

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
# ChatGPTのAPIを呼び出す
###########################
use_secret()

###########################
# コンテンツ
###########################
st.title("Webアプリの説明")
st.divider()
## dfがセッションステートに保存されており、かつ空のファイルではない場合
if 'df' in st.session_state and st.session_state.df is not None:
    st.write(f"アップロードした以下のデータに対して分析を実施中です(データサイズ: {st.session_state.df.shape})")
    st.dataframe(st.session_state.df.head())

st.header("📁csvアップロード")
st.markdown("- このページから、分析に使用するデータをcsv形式でアップロードしてください")
st.markdown("- アップロード作業を行わないと、他のページで分析をすることができません")
st.markdown(
    """
    - 他のページにアクセスしてから**📁csvアップロード**のページに戻ると、csvアップロードを求める画面が再度表示されます
      - しかし、ホーム画面(本ページ)でdataframeが表示されていれば、そのデータで問題なく分析ができます
    """
)

st.header("🔄データの型変換")
st.markdown("- このページではアップロードしたcsvに対して、カラムごとにデータの型を変換することができます")
st.markdown("- csvアップロード後、各種分析を開始する前に変換を実施してください")

st.header("🔽フィルタリング")
st.markdown("- カラムごとにデータの参照範囲をフィルタリングする際に使用してください")

st.header("📊基礎集計")
st.markdown(
    """
    - このページでは基本的な統計量やグラフの描画を行うことができます
      - 1変数の統計量の算出・描画
      - 2変数の値の関係性(相関係数など)
      - 3変数の値の関係性(クロス集計など)
    """
)
st.markdown("- 作成したグラフやデータフレームをダウンロードすることも可能です")

st.header("🤖チャットボット")
st.markdown(
    """
    - このアプリでは、チャットボットに分析の内容を入力すると、
    ChatGPTが対応するPythonコードを生成し、そのコードを実行して結果を表示します。
    """
)

