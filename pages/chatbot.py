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
clear_conversation = st.button("会話の履歴をリセットする", key="clear_conversation")
# チャットの開始(st.session_state.messagesの初期化)
fc.init_messages(clear_conversation)

###########################
# チャットボットのUIを構築
###########################
# チャットメッセージを表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ユーザーからの入力を受け付ける
if user_input := st.chat_input("分析内容を入力してください"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 入力を受け付けた後コードを生成&表示する
    with st.spinner("ChatGPTがコードを生成中です…"):
        generated_code = fc.generate_code(user_input)
        st.session_state.messages.append({"role": "assistant", "content": generated_code})
        with st.chat_message("assistant"):
            st.write(f"生成されたコード:\n")
            st.code(generated_code, language="python")

        # コード生成後、実行結果を表示する
        st.info("生成されたコードを実行中…")
        result = fc.execute_code(generated_code)
        st.session_state.messages.append({"role": "assistant", "content": result})
        with st.chat_message("assistant"):
            try:
                st.code(result)
            except:
                st.write(result)
        
        # エラーが出た場合、その内容をもとにコード修正 & 再実行をする
        if "Error" in result:
            st.session_state.messages.append({"role": "user", "content": "正しく実行ができていないため、エラー内容をもとに自動でコードの修正を実施中"})
            with st.chat_message("user"):
                st.markdown("正しく実行ができていないため、エラー内容をもとに自動でコードの修正を実施中")
            # コードを生成
            generated_code = fc.re_generate_code(generated_code, result)
            st.session_state.messages.append({"role": "assistant", "content": generated_code})
            with st.chat_message("assistant"):
                st.write(f"生成されたコード:\n")
                st.code(generated_code, language="python")
            # 実行結果を出力
            result = fc.execute_code(generated_code)
            st.session_state.messages.append({"role": "assistant", "content": result})
            with st.chat_message("assistant"):
                try:
                    st.code(result)
                    st.error("自動実行でエラーが解消されなかったので、再度指示を入力してください")
                except:
                    st.write(result)
                    st.error("自動実行でエラーが解消されなかったので、再度指示を入力してください")