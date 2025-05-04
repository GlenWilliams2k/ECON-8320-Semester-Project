import pandas as pd
import numpy as np
import requests
import os
import sys
import re

def main():
    if len(sys.argv) < 2:
        raise ValueError("❌ No input file provided. Usage: python clean_data_script.py <input_file>")

    input_file = sys.argv[1]
    output_file = os.path.splitext(input_file)[0] + "_CLEANED.csv"
    sheet_name = "PA Log Sheet" if input_file.endswith(".xlsx") else None

    cleaned_df = clean_data(input_file, sheet_name=sheet_name)
    cleaned_df.to_csv(output_file, index=False)
    print(f"✅ Cleaned {input_file} -> {output_file}")

if __name__ == "__main__":
    main()

#function to fetch zip codes
def fetch_zip_info(zip_codes):
    """Fetch city and state info for zip codes."""
    zip_to_locale = {}
    for zip_code in zip_codes:
        try:
            url = f"https://api.zippopotam.us/us/{zip_code}"
            response = requests.get(url)
            if response.status_code == 200:
                zip_data = response.json()
                city = zip_data['places'][0]['place name']
                state = zip_data['places'][0]['state abbreviation']
                zip_to_locale[zip_code] = {'City': city, 'State': state}
            else:
                zip_to_locale[zip_code] = {'City': 'Unknown', 'State': 'Unknown'}
        except Exception:
            zip_to_locale[zip_code] = {'City': 'Error', 'State': 'Error'}
    return zip_to_locale

def clean_data(filepath, sheet_name="None"):
    """Clean the service learning data."""
    today = pd.Timestamp.today()

    # Read file (Excel or CSV)
    if filepath.endswith('.xlsx'):
        data = pd.read_excel(filepath, sheet_name=sheet_name)
    elif filepath.endswith('.csv'):
        data = pd.read_csv(filepath)
    else:
        raise ValueError("Unsupported file format: Only .csv or .xlsx allowed.")

    # Clean Payment Submitted Date
    def extract_date(text):
        if isinstance(text, pd.Timestamp):
            return text.strftime("%m/%d/%Y")
        match = re.search(r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b', str(text))
        return match.group(0) if match else None
    # Extract dates
    data['Payment Submitted Date'] = data['Payment Submitted?'].apply(extract_date)
    # Convert to datetime
    data['Payment Submitted Date'] = pd.to_datetime(data['Payment Submitted Date'], errors='coerce')
    # Ensure the column is explicitly set to 'Yes' if a valid date was found
    has_date = data['Payment Submitted Date'].notna()
    data.loc[has_date, 'Payment Submitted?'] = 'Yes'

    # Clean Zip, City, State
    data['Pt Zip'] = data['Pt Zip'].astype(str).str.strip().str.extract(r'(\d{5})')[0]
    data['Pt Zip'] = data['Pt Zip'].fillna("Missing")

    data.loc[data['Pt Zip'] == "Missing", ['Pt City', 'Pt State']] = "Missing"

    valid_zips = data[data['Pt Zip'] != "Missing"]['Pt Zip'].unique()
    zip_to_locale = fetch_zip_info(valid_zips)

    data['Pt City'] = data['Pt Zip'].apply(lambda z: zip_to_locale.get(z, {}).get('City', 'Missing'))
    data['Pt State'] = data['Pt Zip'].apply(lambda z: zip_to_locale.get(z, {}).get('State', 'Missing'))

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
    
    data['Patient Letter Notified? (Directly/Indirectly through rep)'] = data['Patient Letter Notified? (Directly/Indirectly through rep)'].apply(letter_notified)
       
    #Clean Payable to:
    # Replace blanks or whitespace-only strings with "Missing"
    data['Payable to:'] = data['Payable to:'].replace(r'^\s*$', "Missing", regex=True)

    # Export cleaned data for testing
    #output_path = r"C:\Users\Glen\Documents\Tools For Data Analysis\Semester Project\cleaned_data.csv"
    #data.to_csv(output_path, index=False)

    #Export cleaned data as part of github action
    output_path = os.path.join("output", "cleaned_data.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    data.to_csv(output_path, index=False)
    
    return data