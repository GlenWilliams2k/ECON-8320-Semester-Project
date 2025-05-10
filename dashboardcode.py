#code to run
#streamlit run dashboard "c:\Users\Glen\Documents\Tools for Data Analysis\Semester Project\dashboardcode.py"
#pip install streamlit
import streamlit as st
import pandas as pd
import glob
import os

#for later use
# Find all CSV files ending in _CLEANED.csv in the current directory
cleaned_files = glob.glob("*_CLEANED.csv")
#Print which files are being read
#print(f"Found cleaned files: {cleaned_files}")
# Combine them into a single DataFrame
df_list = [pd.read_csv(f) for f in cleaned_files]
db_data = pd.concat(df_list, ignore_index=True)

#load data
#db_data = pd.read_csv("C:\\Users\\Glen\\Documents\\ToolsForDataAnalysis\\SemesterProject\\cleaned_data.csv")

st.set_page_config(
    page_title = "Nebraska Cancer Specialists Hope Foundation Dashboard",
    layout = "wide")
st.title("Nebraska Cancer Specialists Hope Foundation Dashboard")

#Page navigation
page = st.sidebar.radio("Select a Page", ["Pending Applications", "Executive Impact Summary"])

# Pending Applications Page - page 1
if page == "Pending Applications":
    st.header("Pending Applications")
        # Filter by "Application Signed?"
        signature_options = ["All"] + list(pd.unique(db_data["Application Signed?"]))
        signed_filter = st.selectbox("Filter by Signature Status:", signature_options)
        if signed_filter != "All":
            db_data = db_data[db_data["Application Signed?"] == signed_filter]
    
    #page 1 dataframe
    db_data_pending = db_data[db_data["Request Status"] == "Pending"]
    #create page 1 card dfs
    pending_apps = db_data_pending["Patient ID#"].nunique()
    signed_apps = db_data_pending[db_data_pending["Application Signed?"] == "YES"]["Patient ID#"].nunique()
    missing_apps = db_data_pending[db_data_pending["Application Signed?"] == "MISSING"]["Patient ID#"].nunique()
    unsigned_apps = db_data_pending[db_data_pending["Application Signed?"] == "NO"]["Patient ID#"].nunique()
    #create page 1 cards
    kpi1, kpi2, kpi3, kpi4, = st.columns(4)
    kpi1.metric(label = "Pending Applications", value = pending_apps)
    kpi2.metric(label = "Signed Pending Applications", value = signed_apps)
    kpi3.metric(label = "Pending Unsigned Applications", value = unsigned_apps)
    kpi4.metric(label = "Pending Applications Missing Signature Status", value = missing_apps)
    
    #Streamlit Dataframe filtered to only pending applications
    pg1_df = db_data[db_data["Request Status"] == "Pending"][
        ["Patient ID#", "Grant Req Date", "Application Signed?", "Pt Zip", "Insurance Type", 
         "Total Household Gross Monthly Income", "Type of Assistance (CLASS)", "Amount", 
         "Referral Source", "Notes"]]
    pg1 = st.data_editor(pg1_df)
    
    #grouping assitance type by amount
    p1_bar_data = pg1.groupby("Type of Assistance (CLASS)")["Amount"].sum().reset_index()
    
    #streamlit barchart for assitance type by amount
    p1_bar = st.bar_chart(data = p1_bar_data, x="Type of Assistance (CLASS)", y="Amount", x_label = "Assistance Type", y_label = "Amount Requested", horizontal = False)

#page 2

#Executive Impact Summary Page - page 4
elif page == "Executive Impact Summary":
    st.header("Exective Impact Summary")
    #page 4 dataframe
    pg4_df = db_data[db_data["Request Status"] == "Approved"]
    pg4_df["City, State"] = pg4_df["Pt City"] + " , " + pg4_df["Pt State"] .fillna('')
    #page 4 card dataframes
    total_amt_awarded_df= pg4_df["Amount"].sum().round()
    total_applicants_awarded_df = pg4_df["Patient ID#"].nunique()
    total_amount = pg4_df["Amount"].sum()
    num_unique_patients = pg4_df["Patient ID#"].nunique()
    avg_award = (total_amount / num_unique_patients).round(2)
    #page 4 cards
    kpi5, kpi6, kpi7 = st.columns(3)
    kpi5.metric(label = "Total Assistance Awarded", value = total_amt_awarded_df)
    kpi6.metric(label = "Total Applicants Awarded", value = total_applicants_awarded_df)
    kpi7.metric(label = "Average Assistance Amount per Patient", value = avg_award)
    
    #bar graph of contribution by insurance type
    p4_bar1_data = pg4_df.groupby("Insurance Type")["Amount"].sum().reset_index()
    p4_bar1 = st.bar_chart(data = p4_bar1_data, x = "Insurance Type", y = "Amount")
    #bar graph of contribution by assistance type
    p4_bar2_data = pg4_df.groupby("Type of Assistance (CLASS)")["Amount"].sum().reset_index()
    p4_bar2 = st.bar_chart(data = p4_bar2_data, x = "Type of Assistance (CLASS)", y = "Amount", x_label = "Assistance Type", y_label = "Amount Approved" )
    #bar graph of contribution by city, state
    p4_bar3_data = pg4_df.groupby("City, State")["Amount"].sum().reset_index().sort_values(by = "Amount", ascending = False).head(20)
    p4_bar3 = st.bar_chart(data = p4_bar3_data, x = "City, State", y = "Amount")
