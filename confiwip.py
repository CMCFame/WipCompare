import streamlit as st
import pandas as pd
from typing import Tuple, List, Dict
import json
import os
import csv

def extract_acronym(file_name: str) -> str:
    if 'PROD' in file_name:
        return 'PROD'
    elif 'QA' in file_name:
        return 'QA'
    else:
        return 'UNKNOWN'

def find_id_column(df: pd.DataFrame) -> str:
    for col in df.columns:
        if "Id" in col:
            return col
    raise ValueError("No column containing 'Id' found")

def detect_csv_dialect(file_path: str) -> csv.Dialect:
    with open(file_path, 'r', newline='') as csvfile:
        sample = csvfile.read(1024)
        return csv.Sniffer().sniff(sample)

@st.cache_data
def load_and_prepare_dataframe(file_path: str, header_row: int) -> pd.DataFrame:
    dialect = detect_csv_dialect(file_path)
    
    # Read the first few lines to determine the actual header row
    with open(file_path, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile, dialect)
        for _ in range(header_row):
            next(reader)
        header = next(reader)
    
    # Now read the CSV file with the correct dialect and header
    df = pd.read_csv(file_path, header=None, names=header, skiprows=header_row+1, dialect=dialect.__dict__)
    
    id_col = find_id_column(df)
    df.set_index(id_col, inplace=True)
    return df

# ... (rest of the functions remain the same)

def main():
    st.title('Enhanced CSV File Comparison Tool')
    
    config = load_config()
    
    uploaded_file1 = st.file_uploader("Choose the first CSV file", type="csv")
    uploaded_file2 = st.file_uploader("Choose the second CSV file", type="csv")
    
    header_row = st.number_input("Header Row (0-based index)", min_value=0, value=config.get('header_row', 4))
    
    if uploaded_file1 is not None and uploaded_file2 is not None:
        try:
            acronym1 = extract_acronym(uploaded_file1.name)
            acronym2 = extract_acronym(uploaded_file2.name)

            # Save uploaded files to disk temporarily
            with open("temp_file1.csv", "wb") as f:
                f.write(uploaded_file1.getbuffer())
            with open("temp_file2.csv", "wb") as f:
                f.write(uploaded_file2.getbuffer())

            df_preview = load_and_prepare_dataframe("temp_file1.csv", header_row)
            columns_to_compare = st.multiselect("Select columns to compare", df_preview.columns.tolist(), default=config.get('columns_to_compare', []))
            
            if st.button("Compare Files"):
                with st.spinner('Processing...'):
                    result_df = compare_csv_files("temp_file1.csv", "temp_file2.csv", acronym1, acronym2, header_row, columns_to_compare)
                    filtered_result_df = filter_empty_rows(result_df)
                    
                    st.success('Comparison complete!')
                    st.subheader("Comparison Results")
                    st.dataframe(filtered_result_df.style.applymap(lambda x: 'background-color: yellow' if '/' in str(x) else ''))
                    
                    visualize_differences(filtered_result_df)
                    
                    st.download_button(
                        label="Download CSV",
                        data=filtered_result_df.to_csv(index=False).encode('utf-8'),
                        file_name='differences_combined_values.csv',
                        mime='text/csv',
                    )
                    
                    # Save configuration
                    new_config = {'header_row': header_row, 'columns_to_compare': columns_to_compare}
                    save_config(new_config)
                    st.success("Comparison settings saved for future use.")

            # Clean up temporary files
            os.remove("temp_file1.csv")
            os.remove("temp_file2.csv")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
