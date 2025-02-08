import streamlit as st 
import traceback
import ast
# LangChainとOpenAI関連のインポート
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate, FewShotPromptTemplate
from langchain.chains import LLMChain, ConversationChain
from langchain_experimental.utilities import PythonREPL
from langchain.agents import Tool
from langchain.memory import ConversationBufferMemory
from langchain.memory import ConversationSummaryMemory
from langchain.schema import SystemMessage
from langchain.schema import HumanMessage, OutputParserException
from langchain.output_parsers import RegexParser

###########################
# APIの取得
########################### 
def use_secret():
    api_key = st.secrets["OPENAI_API_KEY"]

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
# 生成されたコードが parsed_output にテキストとして格納されている場合に追加対応を行う関数
def remove_surrounding_quotes_if_needed(parsed_output: str) -> str:
    # ast.literal_eval でパースできる（= 有効な文字列リテラル）か試す
    try:
        # もし先頭と末尾がダブルクォートやシングルクォートで囲まれた文字列なら
        # ここで実際の文字列(例: import pandas as pd\n...)に変換される
        code_str = ast.literal_eval(parsed_output)
        # 変換できたら、それを返す
        return code_str
    except (SyntaxError, ValueError):
        # もしパースできなかった場合は、もともとの文字列をそのまま返す
        return parsed_output

@st.fragment
def generate_code(analysis_query, summary_flag=False):
    # --- Few-shot で与える入出力例の定義 ---
    examples = [
        {
            "analysis_query": "累積の売り上げ金額がtop10のユーザーを抽出し、その課金額を集計してください",
            "code": (
               """
                import pandas as pd
                import numpy as np
                import streamlit as st

                df = st.session_state.df.copy()

                # 売り上げ金額を計算
                df['Sales'] = df['Quantity'] * df['Unit_Price']

                # ユーザーごとの累積売り上げ金額を計算
                user_sales = df.groupby('Customer_ID')['Sales'].sum().sort_values(ascending=False)

                # 売り上げ金額がtop10のユーザーを抽出
                top10_users = user_sales.head(10)

                result = [top10_users]

                for element in result:
                    st.write(element)
               """
            )
        },
        {
            "analysis_query": "累積の売り上げ金額がtop10のユーザーを抽出し、該当ユーザーの月次の売上推移を折れ線グラフで可視化してください。",
            "code": (
                """
                import pandas as pd
                import numpy as np
                import streamlit as st
                import matplotlib.pyplot as plt

                df = st.session_state.df.copy()

                # 売り上げ金額を計算
                df['Sales'] = df['Quantity'] * df['Unit_Price']

                # ユーザーごとの累積売り上げ金額を計算
                user_sales = df.groupby('Customer_ID')['Sales'].sum().sort_values(ascending=False)

                # 売り上げ金額がtop10のユーザーを抽出
                top10_users = user_sales.head(10)

                # 該当ユーザーの月次の売上推移を計算
                df['Invoice_Month'] = df['Invoice_Date'].dt.to_period('M')
                monthly_sales = df[df['Customer_ID'].isin(top10_users.index)].groupby(['Invoice_Month', 'Customer_ID'])['Sales'].sum().unstack()

                # 折れ線グラフで可視化
                fig, ax = plt.subplots(figsize=(10, 6))
                monthly_sales.plot(ax=ax)
                plt.title('Monthly Sales Trend of Top 10 Users')
                plt.xlabel('Month')
                plt.ylabel('Sales')
                plt.legend(title='Customer ID', bbox_to_anchor=(1.05, 1), loc='upper left')

                result = [top10_users, fig]

                for element in result:
                    if isinstance(element, pd.DataFrame) or isinstance(element, pd.Series):
                        st.write(element)
                    else:
                        st.pyplot(element)
                """
            )
        }
    ]

    # --- 各入出力例のフォーマット定義 ---
    example_prompt = PromptTemplate(
        input_variables=["analysis_query", "code"],
        template="""
                【分析要求の例】
                {analysis_query}

                【生成されたコードの例】
                ```python
                {code}
                """
    )

    # --- Few-shot プロンプト全体の構成 ---
    prefix = """
        DataFrame 'st.session_state.df' には、以下のカラムが存在します。

        - 数値型カラム: {numeric_columns}
        - 文字列型カラム: {non_numeric_columns}
        - 日付型カラム: {datetime_columns}

        上記の前提で、後述の要件を満たすPythonのコードを作成してください。

        # **入出力の例**
    """

    suffix = """
        # **要件の詳細**
        - 過去に実行したコードがある場合は、そのコードをベースに書き換えを実施してください
        - 分析結果の解釈に必要な数値やグラフは漏れが無いように出力してください。
        - 加工するDataFrameは変数 `st.session_state.df` であり、結果は変数 `result` に格納するものとします。  
        - 必要に応じて、以下のライブラリを利用してください。
          - pandas
          - numpy
          - scikit-learn
          - statsmodels
        - コードの出力形式の指定
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

    few_shot_prompt = FewShotPromptTemplate(
        examples=examples,
        example_prompt=example_prompt,
        prefix=prefix,
        suffix=suffix,
        example_separator="\n\n",
        input_variables=["numeric_columns", "non_numeric_columns", "datetime_columns", "analysis_query"]
    )
    
    # --- プロンプトに変数を埋め込み、フォーマット指示を追加 ---
    filled_prompt = few_shot_prompt.format(
        numeric_columns=st.session_state.numeric_columns,
        non_numeric_columns=st.session_state.non_numeric_columns,
        datetime_columns=st.session_state.datetime_columns,
        analysis_query=analysis_query
    )

    # パーサーが指定する出力フォーマットの指示を取得
    format_instructions = (
        "以下のフォーマットに従って、回答を出力してください。\n"
        "必ず python のコードのみを返し、コード以外の説明は入れないでください。\n"
        "出力形式:\n"
        "```python\n<生成されたコード>\n```"
    )
    full_prompt = filled_prompt + "\n\n" + format_instructions

    # --- LangChainのChatOpenAI を利用 ---
    llm = ChatOpenAI(
        temperature=0,
        model_name="gpt-4",
        openai_api_key=st.secrets["OPENAI_API_KEY"]
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
        parsed_output["code"] = remove_surrounding_quotes_if_needed(parsed_output["code"])
        return parsed_output["code"]
    except OutputParserException as e:
        generated_response = remove_surrounding_quotes_if_needed(generated_response)
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
        # TracebackException を使って、例外チェーンなど詳細な情報を取得する
        tb_exception = traceback.TracebackException.from_exception(e)
        detailed_error_trace = ''.join(tb_exception.format(chain=True))
        st.error("コードの実行中にエラーが発生しました。再生成を試みます。")
        st.error("Error:\n" +  detailed_error_trace)
        return  detailed_error_trace
    
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
        # コードの出力形式の指定
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
        openai_api_key=st.secrets["OPENAI_API_KEY"]
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
        parsed_output["code"] = remove_surrounding_quotes_if_needed(parsed_output["code"])
        return parsed_output["code"]
    except OutputParserException as e:
        generated_response = remove_surrounding_quotes_if_needed(generated_response)
        return generated_response.strip()
