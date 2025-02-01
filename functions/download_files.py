import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

# index_flag→csvファイルをダウンロードする際に使用
@st.fragment
def download_file(file, filename, key, index_flag=False):
    if isinstance(file, pd.DataFrame):
        # DataFrameの場合
        csv = file.to_csv(index=index_flag)
        st.download_button(
            label=":red[**データをCSVとしてダウンロード**]",
            data=csv,
            file_name=filename+".csv",
            mime='text/csv',
            key=key
        )
    elif isinstance(file, plt.Figure):
        # Figureの場合
        buf = io.BytesIO()
        file.savefig(buf, format='png')
        buf.seek(0)
        st.download_button(
            label=":red[**グラフをPNG画像としてダウンロード**]",
            data=buf,
            file_name=filename+".png",
            mime='image/png',
            key=key
        )
    else:
        st.error("Unsupported file type")