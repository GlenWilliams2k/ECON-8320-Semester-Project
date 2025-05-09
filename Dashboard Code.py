pip install streamlit
import streamlit as st
import pandas as pd
import plotly.express as px
import glob
import os

#for later use
# Find all CSV files ending in _CLEANED.csv in the current directory
#cleaned_files = glob.glob("*_CLEANED.csv")
#Print which files are being read
#print(f"Found cleaned files: {cleaned_files}")
# Combine them into a single DataFrame
#df_list = [pd.read_csv(f) for f in cleaned_files]
#db_data = pd.concat(df_list, ignore_index=True)

db_data = pd.read_csv("cleaned_data.csv")

st.set_page_config(
    page_title = "Nebraska Cancer Specialists Hope Foundation Dashboard",
    layout = "wide")
st.title("Nebraska Cancer Specialists Hope Foundation Dashboard")
signed_filter = st.selectbox("Filter by Signature", pd.unique(db_data["Application Signed?"]))
db_data = db_data[db_data["Application Signed?"] == signed_filter]