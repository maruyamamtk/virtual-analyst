import streamlit as st
import pandas as pd
import sys
import io

# LangChainとOpenAI関連のインポート
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_experimental.utilities import PythonREPL
from langchain.agents import Tool

from functions.multi_pages import multi_page
 
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
# チャットボットのUIを構築
###########################
st.title("データ分析Webアプリ")
analysis_query = st.text_area("【分析内容の指示】\n実施したい分析内容を入力してください。", height=150)

if st.button("分析を実行"):
    if not analysis_query.strip():
        st.error("分析内容を入力してください。")
    else:
        with st.spinner("ChatGPTがコードを生成中です…"):
            # --- ChatGPTへ送るプロンプトの作成 ---
            # ユーザーの分析要求と、dfの概要情報（カラム名）をプロンプトに含めています。
            prompt_template = f"""
                DataFrame 'st.session_state.df' には、以下のカラムが存在します。

                - 数値型カラム: {st.session_state.numeric_columns}
                - 文字列型カラム: {st.session_state.non_numeric_columns}
                - 日付型カラム: {st.session_state.datetime_columns}

                上記の前提で、後述の要件を満たすPythonのコードを作成してください。
                # ユーザーからの分析要求
                -----------------------
                {analysis_query}
                -----------------------
                # 詳細な要件
                - 分析結果の解釈に必要な数値やグラフは漏れが無いように出力してください。
                - 加工するDataFrameは変数 `st.session_state.df` であり、結果は変数 `result` に格納するものとします。  
                - 必要に応じて、以下のライブラリを利用してください。
                  - pandas
                  - numpy
                  - scikit-learn
                  - statsmodels
                - 以下の形式でコードのみ出力してください:
                ```
                # 必要なライブラリは追加でimportしてください
                import pandas as pd
                import numpy as np
                import streamlit as st
                # ここにコードを書く
                result = [] # 出力したい実行結果を格納するリスト。必要なオブジェクトを適宜appendしていく
                
                # コードの最後の処理は必ず以下のように指定する
                for element in result:
                    # streamlitの関数を使って、適切に出力・描画をしてください
                    print(result)
                ```
            """

        prompt = PromptTemplate(
            input_variables=[
                "numeric_columns",
                "non_numeric_columns",
                "datetime_columns",
                "analysis_query"
                ],
            template=prompt_template
        )

        # --- LangChainのChatOpenAIを利用 ---
        # APIキーは st.secrets などで管理してください
        llm = ChatOpenAI(
            temperature=0, 
            model_name="gpt-3.5-turbo", 
            openai_api_key="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"
            # openai_api_key=st.secrets["OPENAI_API_KEY"]  # secrets管理されたAPIキーを利用
        )

        chain = LLMChain(llm=llm, prompt=prompt)

        # プロンプト変数を埋め込んでChatGPTへ問い合わせ
        generated_response = chain.run({
            "numeric_columns": st.session_state.numeric_columns,
            "non_numeric_columns": st.session_state.non_numeric_columns,
            "datetime_columns": st.session_state.datetime_columns,
            "analysis_query": analysis_query
        })

        # 生成されたコードを画面に表示
        st.subheader("生成されたコード")
        st.code(generated_response, language="python")

        # --- 生成されたコードの実行 ---
        st.info("生成されたコードを実行中…")
        python_repl = PythonREPL()
        result = python_repl.run(generated_response)
        print(result)