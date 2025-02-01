import streamlit as st 
import traceback
# LangChainとOpenAI関連のインポート
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, ConversationChain
from langchain_experimental.utilities import PythonREPL
from langchain.agents import Tool
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage

###########################
# チャットボットとしての基本機能
########################### 
# メッセージを初期化する関数
def init_messages(clear_conversation):
    if clear_conversation == True or "messages" not in st.session_state:
        st.session_state.messages = []

# chatの履歴を格納する関数
def get_chat_history():
    chat_history = []
    start_index = max(0, len(st.session_state.messages)-7) # 直近7回分のやり取りを記憶して回答する
    for i in range(start_index, len(st.session_state.messages)-1):
        chat_history.append(st.session_state.messages[i])
    return chat_history

###########################
# コード生成に使用する関数
###########################
def generate_code(analysis_query):
    # --- ChatGPTへ送るプロンプトの作成 ---
    prompt_template = """
        DataFrame 'st.session_state.df' には、以下のカラムが存在します。

        - 数値型カラム: {numeric_columns}
        - 文字列型カラム: {non_numeric_columns}
        - 日付型カラム: {datetime_columns}

        上記の前提で、後述の要件を満たすPythonのコードを作成してください。
        # ユーザーからの分析要求
        -----------------------
        {analysis_query}
        -----------------------
        # 詳細な要件
        - 過去に実行したコードがある場合は、そのコードをベースに書き換えを実施してください
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
            # 例: st.write(element)→テキストの場合
            # 例: st.pyplot(element)→グラフを描画する場合
            print(element)
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
    llm = ChatOpenAI(
        temperature=0, 
        model_name="gpt-4",
        openai_api_key="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"
        #openai_api_key=st.secrets["OPENAI_API_KEY"]
    )
    
    # chat履歴をプロンプト実行時に参照する
    chat_history = get_chat_history()
    memory = ConversationBufferMemory(memory_key="history", return_messages=True)
    # st.session_state.messagesの内容をConversationBufferMemoryに反映
    # langchainの内部では、ユーザー・アシスタントそれぞれのメッセージを個別に追加する必要がある
    for message in st.session_state.messages:
        if message['role'] == 'user':
            memory.chat_memory.add_user_message(message['content'])
        elif message['role'] == 'assistant':
            memory.chat_memory.add_ai_message(message['content'])

    chain = ConversationChain(llm=llm, memory=memory, verbose=True)


    # プロンプト変数を埋め込んでChatGPTへ問い合わせ
    generated_response = chain.predict(
        input = prompt_template.format(
            numeric_columns=st.session_state.numeric_columns,
            non_numeric_columns=st.session_state.non_numeric_columns,
            datetime_columns=st.session_state.datetime_columns,
            analysis_query=analysis_query
        )
    )

    return generated_response

###########################
# 生成したコードを実行する関数
###########################
def execute_code(code):
    python_repl = PythonREPL()
    try:
        result = python_repl.run(code)
        return result
    except Exception as e:
        st.error("コードの実行中にエラーが発生しました。再生成を試みます。")
        st.error("Error:\n" + traceback.format_exc())
        return traceback.format_exc()
    
###########################
# 生成したコードにエラーが出た場合に再生成を試みる関数
###########################
def re_generate_code(generated_code, result):
    prompt_template = """
        下記のコードを実行したところ、後述のエラーが発生しました。
        要因を特定し、コードの修正案を出力してください。
        なお、出力形式はコードのみにしてください。
        # コード
        {code}
        # エラー
        {error}
        # 出力形式
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
            # 例: st.write(element)→テキストの場合
            # 例: st.pyplot(element)→グラフを描画する場合
            print(element)
        ```
    """
    prompt = PromptTemplate(
        input_variables=[
            "code",
            "error"
        ],
        template=prompt_template
    )

    llm = ChatOpenAI(
        temperature=0, 
        model_name="gpt-4",
        openai_api_key="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"
        #openai_api_key=st.secrets["OPENAI_API_KEY"]
    )

    generated_response = llm([
        HumanMessage(content=prompt.format(code=generated_code, error=result))
    ])
    return generated_response.content