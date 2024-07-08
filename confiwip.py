import streamlit as st
import pandas as pd
from typing import Tuple, Optional
import io

def extract_acronym(file_name: str) -> str:
    if 'PROD' in file_name.upper():
        return 'PROD'
    elif 'QA' in file_name.upper():
        return 'QA'
    else:
        return 'UNKNOWN'

def find_id_column(df: pd.DataFrame) -> str:
    id_columns = [col for col in df.columns if 'id' in col.lower()]
    if not id_columns:
        raise ValueError("No column containing 'Id' found")
    return id_columns[0]

def read_csv(file: io.BytesIO) -> pd.DataFrame:
    try:
        return pd.read_csv(file, header=4)
    except pd.errors.EmptyDataError:
        st.error("The uploaded file is empty.")
        return pd.DataFrame()
    except pd.errors.ParserError:
        st.error("Unable to parse the CSV file. Please check the file format.")
        return pd.DataFrame()

def compare_csv_files(file_path_1: io.BytesIO, file_path_2: io.BytesIO, acronym1: str, acronym2: str) -> Optional[pd.DataFrame]:
    df1 = read_csv(file_path_1)
    df2 = read_csv(file_path_2)
    
    if df1.empty or df2.empty:
        return None

    try:
        id_col1 = find_id_column(df1)
        id_col2 = find_id_column(df2)
    except ValueError as e:
        st.error(str(e))
        return None

    df1.set_index(id_col1, inplace=True)
    df2.set_index(id_col2, inplace=True)

    df1_aligned, df2_aligned = df1.align(df2, join='outer', axis=0, fill_value='')
    diff_mask = df1_aligned != df2_aligned
    diff_df = df1_aligned[diff_mask].combine_first(df2_aligned[diff_mask])

    combined_values = []
    for _, row in diff_df.iterrows():
        row_combined = []
        for col in diff_df.columns:
            val1, val2 = df1_aligned.loc[row.name, col], df2_aligned.loc[row.name, col]
            if pd.isna(val1) and not pd.isna(val2):
                row_combined.append(f'{acronym2}: {val2}')
            elif not pd.isna(val1) and pd.isna(val2):
                row_combined.append(f'{acronym1}: {val1}')
            elif not pd.isna(val1) and not pd.isna(val2) and (val1 != val2):
                row_combined.append(f'{acronym1}: {val1} | {acronym2}: {val2}')
            else:
                row_combined.append('')
        combined_values.append(row_combined)

    combined_values_df = pd.DataFrame(combined_values, columns=diff_df.columns, index=diff_df.index)
    combined_values_df.reset_index(inplace=True)
    return combined_values_df

def filter_empty_rows(df: pd.DataFrame) -> pd.DataFrame:
    return df[df.iloc[:, 1:].astype(str).apply(lambda x: x.str.strip().ne('').any(), axis=1)]

def main():
    st.set_page_config(page_title="CSV File Comparison Tool", layout="wide")
    st.title('CSV File Comparison Tool')

    col1, col2 = st.columns(2)
    with col1:
        uploaded_file1 = st.file_uploader("Choose the first CSV file", type="csv")
    with col2:
        uploaded_file2 = st.file_uploader("Choose the second CSV file", type="csv")

    if uploaded_file1 and uploaded_file2:
        try:
            acronym1 = extract_acronym(uploaded_file1.name)
            acronym2 = extract_acronym(uploaded_file2.name)
            
            with st.spinner('Processing...'):
                result_df = compare_csv_files(uploaded_file1, uploaded_file2, acronym1, acronym2)
                if result_df is not None:
                    st.success('Comparison complete!')
                    result_df = filter_empty_rows(result_df)
                    st.dataframe(result_df, use_container_width=True)
                    
                    csv = result_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name='differences_combined_values.csv',
                        mime='text/csv',
                    )
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()