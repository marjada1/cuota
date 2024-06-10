import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import glob
import os

# Define the URLs and corresponding funds
urls_fondos = {
    'A': 'https://www.spensiones.cl/apps/valoresCuotaFondo/vcfAFP.php?tf=A',
    'B': 'https://www.spensiones.cl/apps/valoresCuotaFondo/vcfAFP.php?tf=B',
    'C': 'https://www.spensiones.cl/apps/valoresCuotaFondo/vcfAFP.php?tf=C',
    'D': 'https://www.spensiones.cl/apps/valoresCuotaFondo/vcfAFP.php?tf=D',
    'E': 'https://www.spensiones.cl/apps/valoresCuotaFondo/vcfAFP.php?tf=E'
}

# Manually entered quotas with correct AFP names
manual_quotas = {
    ('UNO', 'A'): '*',
    ('UNO', 'B'): '*',
    ('UNO', 'C'): '*',
    ('UNO', 'D'): '*',
    ('UNO', 'E'): '*',
    ('CAPITAL', 'A'): '*',
    ('CAPITAL', 'B'): '*',
    ('CAPITAL', 'C'): '*',
    ('CAPITAL', 'D'): '*',
    ('CAPITAL', 'E'): '*',
    ('CUPRUM', 'A'): '*',
    ('CUPRUM', 'B'): '*',
    ('CUPRUM', 'C'): '*',
    ('CUPRUM', 'D'): '*',
    ('CUPRUM', 'E'): '*',
    ('HABITAT', 'A'): '*',
    ('HABITAT', 'B'): '*',
    ('HABITAT', 'C'): '*',
    ('HABITAT', 'D'): '*',
    ('HABITAT', 'E'): '*',
    ('MODELO', 'A'): '*',
    ('MODELO', 'B'): '*',
    ('MODELO', 'C'): '*',
    ('MODELO', 'D'): '*',
    ('MODELO', 'E'): '*',
    ('PLANVITAL', 'A'): '*',
    ('PLANVITAL', 'B'): '*',
    ('PLANVITAL', 'C'): '*',
    ('PLANVITAL', 'D'): '*',
    ('PLANVITAL', 'E'): '*',
    ('PROVIDA', 'A'): '*',
    ('PROVIDA', 'B'): '*',
    ('PROVIDA', 'C'): '*',
    ('PROVIDA', 'D'): '*',
    ('PROVIDA', 'E'): '*',
}

def fetch_data():
    # Initialize list to store data from all funds
    dataframes = []
    afp_status = {afp: {fund: 'NOT YET' for fund in urls_fondos.keys()} for afp in set([k[0] for k in manual_quotas.keys()])}
    fund_dates = {}

    # Variable to store the latest available date from web scraping
    latest_date = None

    # Iterate over each URL and fund
    for fund, url in urls_fondos.items():
        try:
            # Perform GET request
            response = requests.get(url, timeout=10)

            # Check if the request was successful
            if response.status_code == 200:
                # Parse HTML content with BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')

                # Find the date
                date_tag = soup.find_all('table', class_='table table-striped table-hover table-bordered table-condensed')[1]
                if date_tag:
                    date_str = date_tag.find_all('center')[0].text.strip().split()[0]
                    if latest_date is None or date_str > latest_date:
                        latest_date = date_str
                    fund_dates[fund] = date_str
                else:
                    date_str = "Date not found"

                # Find the correct table
                table = soup.find_all('table', class_='table table-striped table-hover table-bordered table-condensed')[1]

                # Initialize lists to store data
                afp = []
                quota_value = []
                net_asset_value = []

                # Traverse table rows
                rows = table.find_all('tr')[2:]  # Adjust to include all relevant rows

                for row in rows:
                    columns = row.find_all('td')
                    if len(columns) == 3:  # Ensure the row has 3 columns
                        afp.append(columns[0].text.strip())
                        quota_value.append(columns[1].text.strip())
                        net_asset_value.append(columns[2].text.strip())

                # Create a DataFrame with the data
                df = pd.DataFrame({
                    'A.F.P.': afp,
                    'Quota Value': quota_value,
                    'Net Asset Value': net_asset_value,
                    'Date': [date_str] * len(afp),
                    'Fund': [fund] * len(afp)
                })

                # Add the DataFrame to the list
                dataframes.append(df)

                # Update AFP status
                for a, v in zip(afp, quota_value):
                    status = "OK" if "*" not in v else "NOT YET"
                    afp_status[a][fund] = status

            else:
                st.error(f"Error accessing the page: {response.status_code}")

        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {e}")

    # Concatenate all DataFrames into one and filter by the most recent date
    if dataframes:
        df_consolidated = pd.concat(dataframes, ignore_index=True)
        df_consolidated = df_consolidated[df_consolidated['Date'] == latest_date]
    else:
        st.write("No data could be retrieved from any fund.")
        return None, None, None, None, None

    # Incorporate manually entered quota values into the DataFrame
    afp_manual = []
    quota_value_manual = []
    net_asset_value_manual = []

    for (afp, fund), quota in manual_quotas.items():
        afp_manual.append(afp)
        quota_value_manual.append(quota)
        net_asset_value_manual.append("")

    # Create DataFrame with manually entered data
    if latest_date is not None:
        df_manual = pd.DataFrame({
            'A.F.P.': afp_manual,
            'Quota Value': quota_value_manual,
            'Net Asset Value': net_asset_value_manual,
            'Date': [latest_date] * len(afp_manual),
            'Fund': [fund for (_, fund) in manual_quotas.keys()]
        })
        dataframes.insert(0, df_manual)
    else:
        st.error("Could not determine the latest available date, so manual data cannot be included.")
        return None, None, None, None, None

    # Concatenate all DataFrames into one
    df_consolidated = pd.concat(dataframes, ignore_index=True)

    # Replace quota values of (*) with manually entered values if available
    for index, row in df_consolidated.iterrows():
        if row['Quota Value'] == '(*)':
            manual_value = manual_quotas.get((row['A.F.P.'], row['Fund']), None)
            if manual_value:
                df_consolidated.at[index, 'Quota Value'] = manual_value

    # Prioritize downloaded values over manually entered ones
    df_consolidated.drop_duplicates(subset=['A.F.P.', 'Fund'], keep='last', inplace=True)

    # Save the DataFrame to a CSV file
    file_date = df_consolidated['Date'].iloc[0].replace("/", "-")
    file_name = f"fund_data_{file_date}.csv"
    df_consolidated.to_csv(file_name, index=False)

    return df_consolidated, file_name, afp_status, latest_date

def clean_values(df):
    df['Quota Value'] = df['Quota Value'].apply(lambda x: pd.to_numeric(x.replace('.', '').replace(',', '.'), errors='coerce'))
    return df

def get_file_date(file_name):
    return os.path.splitext(file_name)[0].split('_')[-1]

# Streamlit interface
st.title("Relative Performance of AFPs ✌️")

if st.button('Run Process'):
    df_consolidated, file_name, afp_status, latest_date = fetch_data()

    if df_consolidated is not None:
        # Read and sort available CSV files
        csv_files = glob.glob('fund_data_*.csv')
        csv_files.sort(key=get_file_date)

        # Read the most recent file (current)
        df_current = pd.read_csv(csv_files[-1])

        # Read the file previous to the most recent (yesterday)
        df_previous = pd.read_csv(csv_files[-2])

        # Clean values in both DataFrames
        df_current = clean_values(df_current)
        df_previous = clean_values(df_previous)

        # Check if both DataFrames contain data
        if not df_current.empty and not df_previous.empty:
            # Merge DataFrames based on AFP and Fund
            df_comparison = pd.merge(df_current, df_previous, on=['A.F.P.', 'Fund'], suffixes=('_today', '_yesterday'))

            # Filter rows where 'Quota Value' from both days are numbers (not NaN)
            df_comparison = df_comparison.dropna(subset=['Quota Value_today', 'Quota Value_yesterday'])

            # Calculate performance

            df_comparison['Performance'] = (df_comparison['Quota Value_today'] - df_comparison['Quota Value_yesterday']) / df_comparison['Quota Value_yesterday'] * 100

            # Select columns for the final table
            df_result = df_comparison[['A.F.P.', 'Fund', 'Quota Value_today', 'Quota Value_yesterday', 'Performance', 'Date_today']]

            # Filter data for AFP Provida
            provida_data = df_comparison[df_comparison['A.F.P.'] == 'PROVIDA']

            # Check if there is performance data for AFP Provida
            if not provida_data.empty:
                # Create a table to store performance differences
                funds = df_comparison['Fund'].unique()
                afps = df_comparison['A.F.P.'].unique()
                afps = afps[afps != 'PROVIDA']  # Exclude AFP Provida

                # Initialize the table with NaN
                performance_difference = pd.DataFrame(index=afps, columns=funds, data=pd.NA)

                # Calculate the performance difference relative to AFP Provida
                for fund in funds:
                    provida_performance = provida_data[provida_data['Fund'] == fund]['Performance']
                    if not provida_performance.empty:
                        for afp in afps:
                            afp_performance = df_comparison[(df_comparison['A.F.P.'] == afp) & (df_comparison['Fund'] == fund)]['Performance']
                            if not afp_performance.empty:
                                difference = (provida_performance.values[0] - afp_performance.values[0]) * 100
                                performance_difference.loc[afp, fund] = round(difference, 1)

                # Display the performance difference table relative to Provida
                st.write("Performance Comparison relative to AFP Provida ✌️:")
                st.dataframe(performance_difference)
            else:
                st.write("No performance data for AFP Provida on this day.")

            # Display the latest available date
            st.write(f"Latest available date from web scraping: {latest_date}")

            # Convert AFP status dictionary to a DataFrame
            afp_status_df = pd.DataFrame(afp_status).T
            afp_status_df.index.name = 'AFP'
            afp_status_df.columns.name = 'Fund'
            
            # Display the status of each AFP
            st.write("Status of each AFP:")
            st.dataframe(afp_status_df)
        else:
            st.write("Insufficient data available for comparison.")
