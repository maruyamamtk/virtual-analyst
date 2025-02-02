import streamlit as st
import pandas as pd
import sys
import io
import traceback

# LangChainとOpenAI関連のインポート
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_experimental.utilities import PythonREPL
from langchain.agents import Tool

from functions.multi_pages import multi_page
import functions.func_chatbot as fc

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
# 初期設定
###########################
st.title("Chatbotによる自動分析")
if st.session_state.df is None:
    st.warning(f"csvをアップロードしないと分析ができません", icon=":material/warning:")
with st.expander("チャットの設定"):
    clear_conversation = st.button("会話の履歴をリセットする", key="clear_conversation")
    #summary_conversion = st.toggle("推論時に過去のチャットを要約する")
    summary_conversion = False # 要約すると上手く動かないためコメントアウト
    retry_num = st.number_input("エラー発生時のリトライ回数を入力してください", min_value=1, max_value=5, key="retry_num")

# チャットの開始(st.session_state.messagesの初期化)
fc.init_messages(clear_conversation)

# --- カスタムCSSの追加 ---
st.markdown(
    """
    <style>
    /* チャット入力欄のコンテナをブラウザ下部に固定し、サイドバー分の余白を確保 */
    div[data-testid="stChatInput"] {
        position: fixed;
        bottom: 0;
        left: 350px; /* サイドバーの幅に合わせて調整 */
        width: calc(100% - 300px); /* サイドバーの幅分を除いた幅 */
        background-color: #f0f0f0; /* 淡い灰色 */
        /* padding: 上右下左 の順。左側はアイコン分を確保 */
        padding: 10px 10px 10px 40px;
        height: 80px; /* 縦方向の幅を2倍程度に増加 */
        z-index: 1000;
        box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.1);
    }

    /* チャット送信を表すアイコンを追加 */
    div[data-testid="stChatInput"]::before {
        content: "📤"; /* 送信を表すアイコン。必要に応じて他のアイコンに変更可 */
        position: absolute;
        left: 5px; /* アイコンの位置を微調整 */
        top: 50%;
        transform: translateY(-50%);
        font-size: 24px;
    }

    /* チャットメッセージが入力欄に隠れないよう、下部に余白を確保 */
    div[data-testid="stChatMessage"] {
        margin-bottom: 160px; /* 入力欄の高さに合わせて余白を調整 */
    }
    </style>
    """,
    unsafe_allow_html=True
)


###########################
# チャットボットのUIを構築
###########################
tab_names = ["Chatbot",
         "過去の実行履歴",
         "プロンプト入力時の注意点"]
tab_list = st.tabs(tab_names)

# チャットメッセージを表示
with tab_list[0]:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # ユーザーからの入力を受け付ける
    if user_input := st.chat_input("分析内容を入力してください"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # 入力を受け付けた後、コードを生成&表示する
        with st.spinner("ChatGPTがコードを生成中です…"):
            generated_code = fc.generate_code(user_input, summary_conversion)
            st.session_state.messages.append({"role": "assistant", "content": generated_code})
            with st.chat_message("assistant"):
                st.write("**生成されたコード:**")
                st.code(generated_code, language="python")

            # コード生成後、実行結果を表示する
            st.info("生成されたコードを実行中…")
            result = fc.execute_code(generated_code, user_input)
            st.session_state.messages.append({"role": "assistant", "content": result})
            with st.chat_message("assistant"):
                st.write("**コードの実行結果:**")
                try:
                    st.code(result)
                except:
                    st.write(result)

            # エラーが出た場合、リトライ処理を実施する
            attempt = 1
            # ループは、生成したコードの実行が成功するか、attemptがretry_numに達するまで継続
            while "Error" in result and attempt < retry_num+1:
                user_input_error = f"正しく実行ができていないため、エラー内容をもとに自動でコードの修正を実施中 (再生成{attempt}回目)"
                st.session_state.messages.append({
                    "role": "user",
                    "content": user_input_error
                })
                with st.chat_message("user"):
                    st.markdown(user_input_error)

                # エラー内容をもとにコードの再生成
                generated_code = fc.re_generate_code(generated_code, result, summary_conversion)
                st.session_state.messages.append({"role": "assistant", "content": generated_code})
                with st.chat_message("assistant"):
                    st.write(f"**生成されたコード (再生成{attempt}回目):**")
                    st.code(generated_code, language="python")

                # 再生成したコードを実行
                st.info("生成されたコードを実行中…")
                result = fc.execute_code(generated_code, user_input_error)
                st.session_state.messages.append({"role": "assistant", "content": result})
                with st.chat_message("assistant"):
                    st.write("**コードの実行結果:**")
                    try:
                        st.code(result)
                    except:
                        st.write(result)

                attempt += 1

            # ループ終了後、エラーが残っていればユーザーに通知
            if "Error" in result:
                st.error("自動実行でエラーが解消されなかったので、再度指示を入力してください")


# 例：重い処理を分離するための関数（@st.fragment により UI の変更で再実行されなくなります）
@st.fragment
def run_heavy_code(code):
    python_repl = PythonREPL()
    python_repl.run(code)

# 過去の実行履歴を表示
with tab_list[1]:
    # タイトル用のカラムを用意
    col1_title, col2_title = st.columns([0.9, 0.1])
    with col1_title:
        st.write("**プロンプト毎の実行履歴**")
    with col2_title:
        st.write("**check**")
        
    # 以前の実行結果を全て表示
    if "execution_results" in st.session_state:
        execution_results = st.session_state.execution_results
        # 1-indexed で奇数番の結果（0番目, 2番目, …）をループ
        for i in range(0, len(execution_results), 2):
            num = int((i + 2) / 2)
            # 各行ごとに新たにカラムを生成することで、縦方向の位置を揃える
            row_left, row_right = st.columns([0.9, 0.1])
            
            with row_left:
                # expander を一意に特定するためのラッパーを挿入
                st.markdown(f"<div id='expander_wrapper_{i}'>", unsafe_allow_html=True)
                # 初期状態は閉じた状態 (expanded=False)
                exp = st.expander(f"実行結果 {num}", expanded=False)
                with exp:
                    st.write("**プロンプト**")
                    st.write(execution_results[i])
                    # 次の偶数番の結果が存在する場合は合わせて表示
                    if i + 1 < len(execution_results):
                        st.write("**実行結果**")
                        st.write(execution_results[i + 1])
                        # 重い処理部分は関数 run_heavy_code に任せる（※st.fragment により再実行されません）
                        run_heavy_code(execution_results[i + 1])
                st.markdown("</div>", unsafe_allow_html=True)
                
            with row_right:
                # チェックボックスを縦方向中央に配置するため、flexbox のスタイルでラッピング
                st.markdown(
                    """
                    <div style="display: flex; align-items: center; justify-content: center; height: 100%;">
                    """,
                    unsafe_allow_html=True
                )
                is_important = st.checkbox("", key=f"important_{i}", value=False)
                st.markdown("</div>", unsafe_allow_html=True)
                
            # チェックされている場合、該当 expander のヘッダーに CSS で色を付与する
            if is_important:
                st.markdown(
                    f"""
                    <style>
                    /* id="expander_wrapper_{i}" 内の expander ヘッダー（details > summary）の背景色を変更 */
                    #expander_wrapper_{i} details > summary {{
                        background-color: #ffdddd !important;
                        padding: 5px;
                        border-radius: 5px;
                    }}
                    </style>
                    """,
                    unsafe_allow_html=True
                )

# 注意点をテキストで説明
with tab_list[2]:
    st.markdown("""
        ### 分析結果の整合性について
        - このページでは、ユーザーが入力したプロンプトに沿って出力されたコードをそのまま実行しています
        - そのため、出力されたコードが絶対に正しいことを保証するものではありません。ご了承ください
        - 以下のような方法で使用することをおすすめします
            - pythonが分かるユーザーがコード・出力を確認しながら効率的にアウトプットを出す
            - 整合性よりもスピード感が重視される分析で使用する
            - SQLに習熟していないユーザーが集計・可視化を手軽に行う
        ### プロンプトのコツ
        - このChatbotで、python実行結果のグラフやデータフレームが表示されるのは、streamlitというライブラリを使っているためです
            - 実行しているコード内に以下のような記載がある場合はstreamlitでの出力ができていないので、その旨をプロンプトで指示しなおしてください
                - `plt.figure(hogehoge)`
                - `print(dataframe)`
        - 出力されたpythonのコードの冒頭or末尾に説明の文章が書かれていると、実行がうまくできません
            - それを修正するようなプロンプトを入力してください
        - 結果がおかしいときは以下の対応を推奨します
            - 中間のアウトプット・データフレームをstreamlitで表示するよう指示する
                - この出力結果から意図通りに動いていない理由を推察し、再度指示を行うと上手くいくケースが多いです
            - コードが意図通りに動くように別のページで型変換などの前処理を行う
    """)
    