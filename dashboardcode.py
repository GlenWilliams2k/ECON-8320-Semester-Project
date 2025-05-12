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

st.logo(image="https://www.bricksrus.com/donorsite/images/logo-NCSHF.png", 
        icon_image="https://ncshopefoundation.org/wp-content/uploads/2023/05/sun.webp")

#Page navigation
with st.sidebar:
     page = st.radio("Select a Page", ["Pending Applications", "Assistance Given by Demographics", "Assistance Delivery Duration", "Grant Utilization", "Executive Impact Summary"])
     max_date = db_data['Grant Req Date'].max().date()
     min_date = db_data['Grant Req Date'].min().date()
     default_start_date = min_date  # Show all time by default
     default_end_date = max_date
     start_date = st.date_input("Start date", default_start_date, min_value=db_data['Grant Req Date'].min().date(), max_value=max_date)
     end_date = st.date_input("End date", default_end_date, min_value=db_data['Grant Req Date'].min().date(), max_value=max_date)

#filtering db data based on user selection
db_data = db_data[(db_data['Grant Req Date'].dt.date >= start_date) & (db_data['Grant Req Date'].dt.date <= end_date)]

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
    total_amt_pending = db_data_pending["Amount"].sum().round()
    #create page 1 cards
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric(label = "Pending Applications", value = pending_apps)
    kpi2.metric(label = "Signed Pending Applications", value = signed_apps)
    kpi3.metric(label = "Pending Unsigned Applications", value = unsigned_apps)
    kpi4.metric(label = "Pending Applications Missing Signature Status", value = missing_apps)
    kpi5.metric(label = "Pending Amount Requested", value = f"${total_amt_pending}")
    
    #Dataframe filtered to only pending applications
    pg1_df = db_data[db_data["Request Status"] == "Pending"][
        ["Patient ID#", "Grant Req Date", "Application Signed?", "Pt Zip", "Insurance Type", 
         "Total Household Gross Monthly Income", "Type of Assistance (CLASS)", "Amount", 
         "Referral Source", "Notes"]]
    
    #grouping assitance type by amount
    p1_bar_data = db_data_pending.groupby("Type of Assistance (CLASS)")["Amount"].sum().reset_index()
    #streamlit barchart for assitance type by amount
    p1_bar = st.bar_chart(data = p1_bar_data, x="Type of Assistance (CLASS)", y="Amount", x_label = "Assistance Type", y_label = "Amount Requested", horizontal = False)
    #pending applications table
    pg1 = st.data_editor(pg1_df)
    
#Assistance amount by demographic factors - page 2
elif page == "Assistance Given by Demographics":
    #page header
    st.header("Assistance Given by Demographics")
    #list of demographic factors
    demo = [
        'Gender', 'State', 'Zip Code', 'Hispanic or Latino', 'Sexuality', 'Race', 'Insurance Type', 'Household Gross Monthly Income', 'Marital Status', 'Household Size', 'Age']

    #demographics selectbox
    demo_select = st.selectbox("Select Demographic", demo)

    # filter & display data based on the selected demographic
    if demo_select == "Gender":
        # sum assistance by gender
        gender_assistance = db_data.groupby("Gender")["Amount"].sum()  
        st.bar_chart(gender_assistance)
        st.write(gender_assistance)

    elif demo_select == "Insurance Type":
        insurance_assistance = db_data.groupby("Insurance Type")["Amount"].sum()  
        st.bar_chart(insurance_assistance)
        st.write(insurance_assistance)

    elif demo_select == "Sexuality":
        sexuality_assistance = db_data.groupby("Sexual Orientation")["Amount"].sum()  
        st.bar_chart(sexuality_assistance)
        st.write(sexuality_assistance)

    elif demo_select == "Race":
        racial_assistance = db_data.groupby("Race")["Amount"].sum()
        st.bar_chart(racial_assistance)
        st.write(racial_assistance)

    elif demo_select == "Hispanic or Latino":
        ethnicity_assistance = db_data.groupby("Hispanic/Latino")["Amount"].sum()  
        st.bar_chart(ethnicity_assistance)
        st.write(ethnicity_assistance)

    elif demo_select == 'State':
        state_assistance = db_data.groupby("Pt State")["Amount"].sum()
        st.bar_chart(state_assistance)
        st.write(state_assistance)

    elif demo_select == "Zip Code":
        st.header("Assistance by Zip Code")

        # Aggregate the total Amount by Zip Code
        zip_code_assistance = db_data.groupby("Pt Zip")["Amount"].sum()

        #map data
        map_data = db_data[['Latitude', 'Longitude', 'Amount', 'Pt Zip']]
        # Ensure the 'Amount' column is numeric
        map_data["Amount"] = pd.to_numeric(map_data["Amount"], errors="coerce")

        # Drop rows without valid zip codes or amount
        map_data = map_data.dropna(subset=["Pt Zip", "Amount", "Latitude", "Longitude"])

        # Create a scatter plot map
        fig = px.scatter_geo(
            map_data, lat="Latitude", lon="Longitude", color="Amount", hover_name="Pt Zip", hover_data=["Amount"], color_continuous_scale="Viridis", projection="albers usa", title="Assistance Amounts by Zip Code",)

        # Update map settings for better visualization
        fig.update_geos(showcoastlines=True, coastlinecolor="Black", showland=True, landcolor="lightgray")
        fig.update_layout(
            geo=dict( projection_type="albers usa", showland=True, landcolor="lightgray", subunitcolor="gray",),
            title_text="Assistance Amounts by Zip Code", coloraxis_colorbar_title="Assistance Amount")
        
        # Display in Streamlit
        st.plotly_chart(fig)
        
        # Show the assistance by Zip Code table
        st.write(zip_code_assistance)

    elif demo_select == "Marital Status":
        marriage_assistance = db_data.groupby('Marital Status')['Amount'].sum()
        st.bar_chart(marriage_assistance)
        st.write(marriage_assistance)

    elif demo_select == "Household Size":
        householdsize_assistance = db_data.groupby('Household Size')['Amount'].sum()
        st.bar_chart(householdsize_assistance)
        st.write(householdsize_assistance) 

#Time to Support - page 3
elif page == "Assistance Delivery Duration":
    st.header("Assistance Delivery Duration")
    #convert request date and payment submitted date to datetime
    db_data["Payment Submitted Date"] = pd.to_datetime(db_data["Payment Submitted Date"], errors='coerce')
    db_data["Grant Req Date"] = pd.to_datetime(db_data["Grant Req Date"], errors='coerce')
    #date difference to get days to assist
    db_data["Time to Assistance"] = (db_data["Payment Submitted Date"] - db_data["Grant Req Date"]).dt.days.round(2)
    #convert results to numeric
    db_data["Time to Assistance"] = pd.to_numeric(db_data["Time to Assistance"])
    #card for average
    kpi9_data = db_data["Time to Assistance"].dropna().mean().round(2)
    kpi9 = st.columns(1)
    kpi9[0].metric(label = "Average Assistance Delivery Duration", value = kpi9_data)
    #histogram of duration
    st.bar_chart(db_data["Time to Assistance"].value_counts().sort_index())

elif page == "Grant Utilization":
    ug_db = db_data[db_data["Remaining Balance"]>0]
    #number of underutilized grants
    underutilized_grants = ug_db["Patient ID#"].nunique()
    #card for underutilized grants
    kpi10 = st.columns(1)
    kpi10[0].metric(label = "Number of Underutlized Grants", value = underutilized_grants)
    #bar chart of underutilization by assistance type
    ug_db_grouped = ug_db.groupby("Type of Assistance (CLASS)")["Amount"].sum().reset_index()
    st.bar_chart(data = ug_db_grouped, x="Type of Assistance (CLASS)", y="Amount", x_label = "Assistance Type", y_label = "Amount Requested", horizontal = False)


#Executive Impact Summary Page - page 5
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
    kpi6, kpi7, kpi8 = st.columns(3)
    kpi6.metric(label = "Total Assistance Awarded", value = f"${total_amt_awarded_df}")
    kpi7.metric(label = "Total Applicants Awarded", value = total_applicants_awarded_df)
    kpi8.metric(label = "Average Assistance Amount per Patient", value = f"${avg_award}")

    #bar graph of contribution by insurance type
    p4_bar1_data = pg4_df.groupby("Insurance Type")["Amount"].sum().reset_index()
    st.subheader("Assistance Given by Insurance Type")
    p4_bar1 = st.bar_chart(data = p4_bar1_data, x = "Insurance Type", y = "Amount")

    #average amount by assistance type
    pg4_df_grouped_avg = pg4_df.groupby("Type of Assistance (CLASS)")["Amount"].mean().reset_index()
    st.subheader("Average Assistance Amount by Type")
    st.bar_chart(data = pg4_df_grouped_avg, x = "Type of Assistance (CLASS)", y = "Amount", x_label = "Assistance Type", y_label = "Amount Approved")
    
    #bar graph of contribution by assistance type
    p4_bar2_data = pg4_df.groupby("Type of Assistance (CLASS)")["Amount"].sum().reset_index()
    st.subheader("Total Assistance by Type")
    p4_bar2 = st.bar_chart(data = p4_bar2_data, x = "Type of Assistance (CLASS)", y = "Amount", x_label = "Assistance Type", y_label = "Amount Approved" )
    
    #bar graph of contribution by top city, state
    p4_bar3_data = pg4_df.groupby("City, State")["Amount"].sum().reset_index().sort_values(by = "Amount", ascending = False).head(20)
    p4_bar3_data = p4_bar3_data.sort_values(by="Amount", ascending=True)
    st.subheader("Total Assistance by Top 20 City and State")
    p4_bar3 = st.bar_chart(data = p4_bar3_data, x = "City, State", y = "Amount")
    
    #bar graph of contribution by bottom city, state
    p4_bar4_data = pg4_df.groupby("City, State")["Amount"].sum().reset_index().sort_values(by = "Amount", ascending = False).tail(20)
    p4_bar4_data = p4_bar4_data.sort_values(by="Amount", ascending=True)
    st.subheader("Total Assistance by Bottom 20 City and State")
    p4_bar4 = st.bar_chart(data = p4_bar4_data, x = "City, State", y = "Amount")
