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
         "過去の実行履歴"]
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
                st.write("生成されたコード:")
                st.code(generated_code, language="python")

            # コード生成後、実行結果を表示する
            st.info("生成されたコードを実行中…")
            result = fc.execute_code(generated_code, user_input)
            st.session_state.messages.append({"role": "assistant", "content": result})
            with st.chat_message("assistant"):
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
                    st.write(f"生成されたコード (再生成{attempt}回目):")
                    st.code(generated_code, language="python")

                # 再生成したコードを実行
                st.info("生成されたコードを実行中…")
                result = fc.execute_code(generated_code, user_input_error)
                st.session_state.messages.append({"role": "assistant", "content": result})
                with st.chat_message("assistant"):
                    try:
                        st.code(result)
                    except:
                        st.write(result)

                attempt += 1

            # ループ終了後、エラーが残っていればユーザーに通知
            if "Error" in result:
                st.error("自動実行でエラーが解消されなかったので、再度指示を入力してください")


# 過去の実行履歴を表示
with tab_list[1]:
    # 以前の実行結果を全て表示
    if "execution_results" in st.session_state:
        st.markdown("### 過去の実行結果")
        execution_results = st.session_state.execution_results
        # 1-indexedで奇数番の結果（すなわち0番目, 2番目, …）をループ
        for i in range(0, len(execution_results), 2):
            with st.expander(f"実行結果 {int((i+2)/2)}"):
                st.write("**プロンプト**")
                st.write(execution_results[i])
                # 直後の偶数番の結果が存在する場合は合わせて表示
                if i + 1 < len(execution_results):
                    st.write("**実行結果**")
                    st.write(execution_results[i+1])
                    python_repl = PythonREPL()
                    python_repl.run(execution_results[i+1])