import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Tuple, List
import json

@st.cache_data
def load_and_prepare_dataframe(file_path: str, header_row: int) -> pd.DataFrame:
    df = pd.read_csv(file_path, header=header_row)
    id_col = find_id_column(df)
    df.set_index(id_col, inplace=True)
    return df

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

def visualize_differences(df: pd.DataFrame):
    diff_counts = df.apply(lambda x: x.astype(str).str.contains('/').sum())
    fig = go.Figure(data=[go.Bar(x=diff_counts.index, y=diff_counts.values)])
    fig.update_layout(title="Differences per Column", xaxis_title="Columns", yaxis_title="Number of Differences")
    st.plotly_chart(fig)

def save_config(config: dict):
    with open('comparison_config.json', 'w') as f:
        json.dump(config, f)

def load_config() -> dict:
    try:
        with open('comparison_config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

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
                    config = {'header_row': header_row, 'columns_to_compare': columns_to_compare}
                    save_config(config)
                    st.success("Comparison settings saved for future use.")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
