import streamlit as st
import pandas as pd
from typing import Tuple, List, Dict
import json
import os

# ... (previous functions remain the same)

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
