import pandas as pd
import numpy as np
import requests
import os
import sys
import re

#function to fetch zip codes
def fetch_zip_info(zip_codes):
    """Fetch city, state, latitude, and longitude for zip codes."""
    zip_to_locale = {}
    for zip_code in zip_codes:
        try:
            url = f"https://api.zippopotam.us/us/{zip_code}"
            response = requests.get(url)
            if response.status_code == 200:
                zip_data = response.json()
                place = zip_data['places'][0]
                city = place['place name']
                state = place['state abbreviation']
                latitude = float(place['latitude'])
                longitude = float(place['longitude'])
                zip_to_locale[zip_code] = {
                    'City': city,
                    'State': state,
                    'Latitude': latitude,
                    'Longitude': longitude
                }
            else:
                zip_to_locale[zip_code] = {
                    'City': 'Unknown',
                    'State': 'Unknown',
                    'Latitude': None,
                    'Longitude': None
                }
        except Exception:
            zip_to_locale[zip_code] = {
                'City': 'Error',
                'State': 'Error',
                'Latitude': None,
                'Longitude': None
            }
    return zip_to_locale

def clean_data(filepath, sheet_name = None):
    """Clean the service learning data."""
    today = pd.Timestamp.today()

    # Read file (Excel or CSV)
    if filepath.endswith('.xlsx'):
        # Safely read Excel with specified sheet name
        xl = pd.ExcelFile(filepath)
        if sheet_name and sheet_name not in xl.sheet_names:
            raise ValueError(f"Sheet '{sheet_name}' not found. Available sheets: {xl.sheet_names}")
        data = xl.parse(sheet_name) if sheet_name else xl.parse(xl.sheet_names[0])
    elif filepath.endswith('.csv'):
        data = pd.read_csv(filepath)
    else:
        raise ValueError("Unsupported file format: Only .csv or .xlsx allowed.")

    # Clean Payment Submitted Date
    # Duplicate Payment Submitted?
    data['Payment Submitted Date'] = data['Payment Submitted?']
    # Convert to datetime and fill non-dates with NaT
    data['Payment Submitted Date'] = pd.to_datetime(data['Payment Submitted Date'], errors='coerce')
    # Ensure the column is explicitly set to 'Yes' if a valid date was found
    data['Payment Submitted?'] = data['Payment Submitted?'].apply(
    lambda x: x if pd.to_datetime(x, errors='coerce') is pd.NaT else 'Yes')

    #Grant Request Date
    data["Grant Req Date"] = pd.to_datetime(data["Grant Req Date"]).dt.strftime('%m/%d/%Y')

    # Clean Zip, City, State
    data['Pt Zip'] = data['Pt Zip'].astype(str).str.strip().str.extract(r'(\d{5})')[0]
    data['Pt Zip'] = data['Pt Zip'].fillna("Missing")
    data.loc[data['Pt Zip'] == "Missing", ['Pt City', 'Pt State']] = "Missing"

    valid_zips = data[data['Pt Zip'] != "Missing"]['Pt Zip'].unique()
    zip_to_locale = fetch_zip_info(valid_zips)

    # Add City, State, Latitude, Longitude
    data['Pt City'] = data['Pt Zip'].apply(lambda z: zip_to_locale.get(z, {}).get('City', 'Missing'))
    data['Pt State'] = data['Pt Zip'].apply(lambda z: zip_to_locale.get(z, {}).get('State', 'Missing'))
    data['Latitude'] = data['Pt Zip'].apply(lambda z: zip_to_locale.get(z, {}).get('Latitude'))
    data['Longitude'] = data['Pt Zip'].apply(lambda z: zip_to_locale.get(z, {}).get('Longitude'))

    # Clean DOB
    data['DOB'] = pd.to_datetime(data['DOB'], errors='coerce')
    data.loc[data['DOB'] > today, 'DOB'] = pd.NaT
 
    # Clean Gender
    data['Gender'] = data['Gender'].replace(r'^\s*$', "Missing", regex=True)

    # Clean Race
    data['Race'] = data['Race'].astype(str).str.strip().str.lower()
    data['Race'] = data['Race'].apply(lambda x: (
        'American Indian or Alaska Native' if 'american indian' in x else
        'White' if x.startswith('w') else
        "Missing" if x in ['', 'nan'] else x.title()
    ))

    # Clean Hispanic/Latino
    data['Hispanic/Latino'] = data['Hispanic/Latino'].astype(str).str.strip().str.lower()
    data['Hispanic/Latino'] = data['Hispanic/Latino'].apply(lambda x: (
        'Non-Hispanic or Latino' if x.startswith('no') else
        'Hispanic or Latino' if not (x.startswith('no') or x in ['nan', '', 'missing', 'decline to answer', 'non-hispanic']) else
        np.nan
    ))

    # Clean Sexual Orientation
    data['Sexual Orientation'] = data['Sexual Orientation'].astype(str).str.strip().str.lower()
    data['Sexual Orientation'] = data['Sexual Orientation'].apply(lambda x: (
        'Decline to answer' if x == 'decline' else
        'Straight' if x.startswith('st') else
        np.nan if x in ['n/a', '', 'nan'] else x.title()
    ))

    # Clean Insurance Type
    data['Insurance Type'] = data['Insurance Type'].astype(str).str.strip().str.lower()
    data['Insurance Type'] = data['Insurance Type'].apply(lambda x: (
        'Medicare & Medicaid' if 'medicare' in x or 'medicaid' in x else
        'Uninsured' if x.startswith('un') else
        'Missing' if x in ['', 'nan'] else
        x.title()
    ))

    # Marital Status, Gender, Hispanic/Latino, Sexual Orientation blanks to "Missing"
    for col in ['Marital Status', 'Gender', 'Hispanic/Latino', 'Sexual Orientation']:
        data[col] = data[col].astype(str).str.strip().replace(r'^\s*$', 'Missing', regex=True).replace('nan', 'Missing')

    # Sexual Orientation further normalization
    data['Sexual Orientation'] = data['Sexual Orientation'].str.lower().apply(lambda x: (
        'Decline to answer' if x == 'decline' else
        'Straight' if x.startswith('st') else
        x.title()
    ))

    # Clean HouseHold Size
    data['Household Size'] = pd.to_numeric(data['Household Size'], errors='coerce')
    data.loc[(data['Household Size'] > 20) | (data['Household Size'].isna()), 'Household Size'] = np.nan

    # Clean Total Household Gross Monthly Income
    data['Total Household Gross Monthly Income'] = (
        data['Total Household Gross Monthly Income']
        .astype(str).str.replace(r'[^\d.]', '', regex=True)
    )
    data['Total Household Gross Monthly Income'] = pd.to_numeric(data['Total Household Gross Monthly Income'], errors='coerce')

    # Clean Distance roundtrip
    data['Distance roundtrip/Tx'] = pd.to_numeric(
        data['Distance roundtrip/Tx'].astype(str).str.extract(r'(\d+\.?\d*)')[0],
        errors='coerce'
    )

    # Clean Referral Source
    data['Referral Source'] = data['Referral Source'].astype(str).str.strip().replace(r'^\s*$', 'Missing', regex=True)

    # Clean Payment Method
    data['Payment Method'] = data['Payment Method'].astype(str).str.strip().replace(r'^\s*$', 'Missing', regex=True).replace('nan', 'Missing')
     # Strip everything except letters
    data['Payment Method'] = data['Payment Method'].str.replace(r'[^a-zA-Z\s]','', regex=True).str.strip()
    #Uppercase
    data['Payment Method'] = data['Payment Method'].str.upper()

    # Clean Remaining Balance
    data['Remaining Balance'] = pd.to_numeric(data['Remaining Balance'], errors='coerce').round(2)
    #Clean Amount
    data['Amount'] = pd.to_numeric(data['Amount'], errors='coerce').round(2)

    # Clean Patient Letter Notified
    def letter_notified(val):
        val = str(val).strip().lower()
        if val in ['na', 'n/a', 'missing', '', 'nan']:
            return 'No'
        try:
            pd.to_datetime(val)
            return 'Yes'
        except:
            return 'No'
    
    #create date notified
    data['Date Notified'] = data['Patient Letter Notified? (Directly/Indirectly through rep)']
    # Convert to datetime and fill non-dates with NaT
    data['Date Notified'] = pd.to_datetime(data['Date Notified'], errors='coerce')
    #cleaning Patiend Letter Notified
    data['Patient Letter Notified? (Directly/Indirectly through rep)'] = data['Patient Letter Notified? (Directly/Indirectly through rep)'].apply(letter_notified)
       
    #Clean Payable to:
    # Replace blanks or whitespace-only strings with "Missing"
    data['Payable to:'] = data['Payable to:'].replace(r'^\s*$', "Missing", regex=True)

    #Clean Application Signed?
    data['Application Signed?'] = data['Application Signed?'].replace(np.nan, "Missing", regex=True)
    data['Application Signed?'] = data['Application Signed?'].str.upper()

    # Clean Type of Assistance
    data['Type of Assistance (CLASS)'] = data['Type of Assistance (CLASS)'].astype(str).str.strip().str.lower()
    data['Type of Assistance (CLASS)'] = data['Type of Assistance (CLASS)'].apply(lambda x: 'utilities' if x.startswith('u') else x)
    data['Type of Assistance (CLASS)'] = data['Type of Assistance (CLASS)'].str.title()

    # Clean Marital Status
    data['Marital Status'] = data['Marital Status'].astype(str).str.strip().str.lower().str.title()
    data['Marital Status'] = data['Marital Status'].apply(lambda x: 'Seperated' if x.startswith('Se') else x)

    # Clean Gender
    data['Gender'] = data['Gender'].astype(str).str.strip().str.lower().str.title()

    # Export cleaned data for testing
    #output_path = r"C:\\Users\\Glen\\Documents\\ToolsForDataAnalysis\\SemesterProject\\cleaned_data.csv"
    #data.to_csv(output_path, index=False)

    #Export cleaned data as part of github action
    output_path = os.path.join("output", "cleaned_data.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    data.to_csv(output_path, index=False)
    
    return data

def main():
    if len(sys.argv) < 2:
        raise ValueError("No input file provided. Usage: python clean_data_script.py <input_file>")

    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file '{input_file}' not found.")

    # Determine output file
    output_file = os.path.splitext(input_file)[0] + "_CLEANED.csv"
    sheet_name = "PA Log Sheet" if input_file.endswith(".xlsx") else None

    print(f"Reading from: {input_file}")
    cleaned_df = clean_data(input_file, sheet_name=sheet_name)

    print(f"Saving cleaned data to: {output_file}")
    cleaned_df.to_csv(output_file, index=False)
    print(f"✅ Cleaning completed: {input_file} -> {output_file}")

if __name__ == "__main__":
    main()
