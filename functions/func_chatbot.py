import streamlit as st 
import traceback
# LangChainとOpenAI関連のインポート
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, ConversationChain
from langchain_experimental.utilities import PythonREPL
from langchain.agents import Tool
from langchain.memory import ConversationBufferMemory
from langchain.memory import ConversationSummaryMemory
from langchain.schema import SystemMessage
from langchain.schema import HumanMessage, OutputParserException
from langchain.output_parsers import RegexParser

###########################
# チャットボットとしての基本機能
########################### 
# メッセージ・コードの実行結果を初期化する関数
@st.fragment
def init_messages(clear_conversation):
    if clear_conversation == True or "messages" not in st.session_state:
        st.session_state.messages = []
    if clear_conversation == True or "execution_results" not in st.session_state:
        st.session_state.execution_results = []

# chatの履歴を格納する関数
@st.fragment
def get_chat_history():
    chat_history = []
    start_index = max(0, len(st.session_state.messages)-7) # 直近7回分のやり取りを記憶して回答する
    for i in range(start_index, len(st.session_state.messages)-1):
        chat_history.append(st.session_state.messages[i])
    return chat_history


###########################
# コード生成に使用する関数
###########################
@st.fragment
def generate_code(analysis_query, summary_flag=False):
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
        - コードの中身についての指定
        ```
        # 必要なライブラリは追加でimportしてください
        import pandas as pd
        import numpy as np
        import streamlit as st
        # データをdfに読み込む
        df = st.session_state.df.copy()
        # ここにコードを書く
        result = [] # 出力したい実行結果を格納するリスト。必要なオブジェクトを適宜appendしていく
        
        # コードの最後の処理は必ず以下のように指定する
        for element in result:
            # streamlitの関数を使って、適切に出力・描画をしてください
            # 例: st.write(element)→テキストの場合
            # 例: st.pyplot(element)→グラフを描画する場合
            st.pyplot(element)
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
    
    # パーサーが指定する出力フォーマットの指示を取得
    format_instructions = (
        "以下のフォーマットに従って、回答を出力してください。\n"
        "必ず python のコードのみを返し、コード以外の説明は入れないでください。\n"
        "出力形式:\n"
        "```python\n<生成されたコード>\n```"
    )
    # --- プロンプトに変数を埋め込み、フォーマット指示を追加 ---
    filled_prompt = prompt.format(
        numeric_columns=st.session_state.numeric_columns,
        non_numeric_columns=st.session_state.non_numeric_columns,
        datetime_columns=st.session_state.datetime_columns,
        analysis_query=analysis_query
    )
    full_prompt = filled_prompt + "\n\n" + format_instructions

    # --- LangChainのChatOpenAI を利用 ---
    llm = ChatOpenAI(
        temperature=0,
        model_name="gpt-4",
        openai_api_key="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"
        #openai_api_key=st.secrets["OPENAI_API_KEY"]
    )
    
    # --- 要約フラグに応じたメモリの設定 ---
    if summary_flag:
        memory = ConversationSummaryMemory(llm=llm, memory_key="history", return_messages=True)
    else:
        memory = ConversationBufferMemory(memory_key="history", return_messages=True)
    
    # --- system向けのプロンプトを追加 ---
    system_message = (
        "あなたは優秀なデータアナリストです。"
        "入力された要件に沿って分析を行うpythonコードを出力してください。"
        "その際、出力はコードのみとし、その他の説明は絶対に含めないで下さい。"
        "分析に使用するデータは常にst.session_state.dfになります。dfにcopy()してから分析を開始してください。"
        "また、実行結果はstreamlitで表示させてください。"
    )
    memory.chat_memory.add_message(SystemMessage(content=system_message))
    
    # st.session_state.messages の内容を ConversationMemory に反映
    for message in st.session_state.messages:
        if message['role'] == 'user':
            memory.chat_memory.add_user_message(message['content'])
        elif message['role'] == 'assistant':
            memory.chat_memory.add_ai_message(message['content'])
    
    # --- ConversationChain の作成 ---
    chain = ConversationChain(llm=llm, memory=memory, verbose=True)
    # --- ChatGPT へ問い合わせ ---
    generated_response = chain.predict(input=full_prompt)
    # --- LLM の出力からコード部分のみを抽出 ---
    # RegexParser の定義（コードブロックの中身を抽出）
    parser = RegexParser(
        # 「```python」と「```」があってもなくてもコード部分をキャプチャする正規表現
        regex=r"^(?:```python\s*)?([\s\S]*?)(?:\s*```)?\s*$",
        output_keys=["code"]
    )
    try:
        parsed_output = parser.parse(generated_response)
        return parsed_output["code"]
    except OutputParserException as e:
        # パースに失敗した場合は、出力全体をコードとみなして返す
        return generated_response.strip()


###########################
# 生成したコードを実行する関数
###########################
@st.fragment
def execute_code(code, user_input):
    python_repl = PythonREPL()
    try:
        result = python_repl.run(code)
        # 結果をセッション状態に保存する(ユーザーの指示と実行結果を交互に保存)
        st.session_state["execution_results"].append(user_input)
        st.session_state["execution_results"].append(code) # コードを保存し、それを実行して表示させる
        return result
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        st.error("コードの実行中にエラーが発生しました。再生成を試みます。")
        st.error("Error:\n" + error_msg)
        return error_msg
    
###########################
# 生成したコードにエラーが出た場合に再生成を試みる関数
###########################
@st.fragment
def re_generate_code(generated_code, result, summary_flag=False):
    prompt_template = """
        下記のコードを実行したところ、後述のエラーが発生しました。
        要因を特定し、コードの修正案を出力してください。
        # コード
        {code}
        # エラー
        {error}
        # コードの中身についての指定
        ```
        # 必要なライブラリは追加でimportしてください
        import pandas as pd
        import numpy as np
        import streamlit as st
        # データをdfに読み込む
        df = st.session_state.df.copy()
        # ここにコードを書く
        result = [] # 出力したい実行結果を格納するリスト。必要なオブジェクトを適宜appendしていく
        
        # コードの最後の処理は必ず以下のように指定する
        for element in result:
            # streamlitの関数を使って、適切に出力・描画をしてください
            # 例: st.write(element)→テキストの場合
            # 例: st.pyplot(element)→グラフを描画する場合
            st.pyplot(element)
        ```
    """

    prompt = PromptTemplate(
        input_variables=["code", "error"],
        template=prompt_template
    )
    # パーサーが指定する出力フォーマットの指示を取得
    format_instructions = (
        "以下のフォーマットに従って、回答を出力してください。\n"
        "必ず python のコードのみを返し、コード以外の説明は入れないでください。\n"
        "出力形式:\n"
        "```python\n<生成されたコード>\n```"
    )
    # --- プロンプトに変数を埋め込み、フォーマット指示を追加 ---
    filled_prompt = prompt.format(
            code=generated_code,
            error=result
    )
    full_prompt = filled_prompt + "\n\n" + format_instructions

    llm = ChatOpenAI(
        temperature=0, 
        model_name="gpt-4",
        openai_api_key="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"
        #openai_api_key=st.secrets["OPENAI_API_KEY"]
    )

    # --- 要約フラグに応じたメモリの設定 ---
    if summary_flag:
        memory = ConversationSummaryMemory(llm=llm, memory_key="history", return_messages=True)
    else:
        memory = ConversationBufferMemory(memory_key="history", return_messages=True)
    
    # --- system向けのプロンプトを追加 ---
    system_message = (
        "あなたは優秀なデータアナリストです。"
        "入力された要件に沿って分析を行うpythonコードを出力してください。"
        "その際、出力はコードのみとし、その他の説明は絶対に含めないで下さい。"
        "分析に使用するデータは常にst.session_state.dfになります。dfにcopy()してから分析を開始してください。"
        "また、実行結果はstreamlitで表示させてください。"
    )
    memory.chat_memory.add_message(SystemMessage(content=system_message))
    
    # st.session_state.messagesの内容をConversationMemoryに反映
    for message in st.session_state.messages:
        if message['role'] == 'user':
            memory.chat_memory.add_user_message(message['content'])
        elif message['role'] == 'assistant':
            memory.chat_memory.add_ai_message(message['content'])
    
    chain = ConversationChain(llm=llm, memory=memory, verbose=True)
    # --- ChatGPT へ問い合わせ ---
    generated_response = chain.predict(input=full_prompt)
    # --- LLM の出力からコード部分のみを抽出 ---
    # RegexParser の定義（コードブロックの中身を抽出）
    parser = RegexParser(
        # 「```python」と「```」があってもなくてもコード部分をキャプチャする正規表現
        regex=r"^(?:```python\s*)?([\s\S]*?)(?:\s*```)?\s*$",
        output_keys=["code"]
    )
    try:
        parsed_output = parser.parse(generated_response)
        return parsed_output["code"]
    except OutputParserException as e:
        # パースに失敗した場合は、出力全体をコードとみなして返す
        return generated_response.strip()
