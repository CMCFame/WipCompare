import streamlit as st
import pandas as pd
from typing import Tuple, List, Dict
import json
import os

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

@st.cache_data
def load_and_prepare_dataframe(file_path: str, header_row: int) -> pd.DataFrame:
    df = pd.read_csv(file_path, header=header_row)
    id_col = find_id_column(df)
    df.set_index(id_col, inplace=True)
    return df

def align_dataframes(df1: pd.DataFrame, df2: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    return df1.align(df2, join='outer', axis=0, fill_value='')

def create_diff_mask(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    return df1 != df2

def combine_differences(df1: pd.DataFrame, df2: pd.DataFrame, diff_mask: pd.DataFrame, acronym1: str, acronym2: str) -> pd.DataFrame:
    combined_values = []
    for i in range(len(diff_mask)):
        row_combined = []
        for col in diff_mask.columns:
            if pd.isna(df1.iloc[i][col]) and not pd.isna(df2.iloc[i][col]):
                row_combined.append(f' / {acronym2}: {df2.iloc[i][col]}')
            elif not pd.isna(df1.iloc[i][col]) and pd.isna(df2.iloc[i][col]):
                row_combined.append(f'{acronym1}: {df1.iloc[i][col]} / ')
            elif not pd.isna(df1.iloc[i][col]) and not pd.isna(df2.iloc[i][col]) and (df1.iloc[i][col] != df2.iloc[i][col]):
                row_combined.append(f'{acronym1}: {df1.iloc[i][col]} / {acronym2}: {df2.iloc[i][col]}')
            else:
                row_combined.append('')
        combined_values.append(row_combined)
    
    combined_values_df = pd.DataFrame(combined_values, columns=diff_mask.columns, index=diff_mask.index)
    combined_values_df.reset_index(inplace=True)
    return combined_values_df

def filter_empty_rows(df: pd.DataFrame) -> pd.DataFrame:
    return df[df.apply(lambda row: row.drop(labels=[df.columns[0]]).astype(str).str.strip().any(), axis=1)]

def compare_csv_files(file_path_1: str, file_path_2: str, acronym1: str, acronym2: str, header_row: int, columns_to_compare: List[str]) -> pd.DataFrame:
    df1 = load_and_prepare_dataframe(file_path_1, header_row)
    df2 = load_and_prepare_dataframe(file_path_2, header_row)
    
    if columns_to_compare:
        df1 = df1[columns_to_compare]
        df2 = df2[columns_to_compare]
    
    df1_aligned, df2_aligned = align_dataframes(df1, df2)
    diff_mask = create_diff_mask(df1_aligned, df2_aligned)
    
    combined_values_df = combine_differences(df1_aligned, df2_aligned, diff_mask, acronym1, acronym2)
    return combined_values_df

def save_config(config: Dict[str, any]):
    with open('comparison_config.json', 'w') as f:
        json.dump(config, f)

def load_config() -> Dict[str, any]:
    if os.path.exists('comparison_config.json'):
        with open('comparison_config.json', 'r') as f:
            return json.load(f)
    return {}  # Return an empty dictionary if the file doesn't exist

def visualize_differences(df: pd.DataFrame):
    diff_counts = df.apply(lambda x: x.astype(str).str.contains('/').sum())
    st.subheader("Differences per Column")
    st.bar_chart(diff_counts)

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

            df_preview = pd.read_csv(uploaded_file1, nrows=10)
            columns_to_compare = st.multiselect("Select columns to compare", df_preview.columns.tolist(), default=config.get('columns_to_compare', []))
            
            if st.button("Compare Files"):
                with st.spinner('Processing...'):
                    result_df = compare_csv_files(uploaded_file1, uploaded_file2, acronym1, acronym2, header_row, columns_to_compare)
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
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
