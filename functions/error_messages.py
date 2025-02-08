import streamlit as st
import pandas as pd

##############################
#
# 全ての関数をst.cache_dataによってキャッシュ化し、実行時間の短縮を試みている
#
##############################

@st.cache_data
def coltype_error(target_coltype):
    if target_coltype == '数値型' and not st.session_state.numeric_columns:
        st.error("数値型のカラムが存在しません。", icon=":material/error:")
        return False
    elif target_coltype == '日付型' and not st.session_state.datetime_columns:
        st.error("日付型のカラムが存在しません。", icon=":material/error:")
        return False
    elif target_coltype == '文字列型' and not st.session_state.non_numeric_columns:
        st.error("文字列型のカラムが存在しません。", icon=":material/error:")
        return False
    else:
        return True
    
@st.cache_data
def all_null_warning(target_coltype):
    output_flag = True
    if target_coltype == '数値型':
        for col in st.session_state.numeric_columns:
            if st.session_state.df[col].isnull().all():
                st.warning(f"{col} カラムの全ての値がnullになっているため、削除します。", icon=":material/warning:")
                st.session_state.df = st.session_state.df.drop(col, axis = 1)
                # filter機能をリセットした際にカラム数に差異が出ないように、df_originalにも処理を実施
                st.session_state.df_original = st.session_state.df_original.drop(col, axis = 1)
                output_flag = False
        return output_flag
    if target_coltype == '日付型':
        for col in st.session_state.datetime_columns:
            if st.session_state.df[col].isnull().all():
                st.warning(f"{col} カラムの全ての値がnullになっているため、削除します。", icon=":material/warning:")
                st.session_state.df = st.session_state.df.drop(col, axis = 1)
                # filter機能をリセットした際にカラム数に差異が出ないように、df_originalにも処理を実施
                st.session_state.df_original = st.session_state.df_original.drop(col, axis = 1)
                output_flag = False
        return output_flag
    if target_coltype == '文字列型':
        for col in st.session_state.non_numeric_columns:
            if st.session_state.df[col].isnull().all():
                st.warning(f"{col} カラムの全ての値がnullになっているため、削除します。", icon=":material/warning:")
                st.session_state.df = st.session_state.df.drop(col, axis = 1)
                # filter機能をリセットした際にカラム数に差異が出ないように、df_originalにも処理を実施
                st.session_state.df_original = st.session_state.df_original.drop(col, axis = 1)
                output_flag = False
        return output_flag
    else:
        return output_flag