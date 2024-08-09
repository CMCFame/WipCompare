import streamlit as st
import pandas as pd

# Function to extract acronyms from filenames
def extract_acronym(file_name):
    if 'PROD' in file_name:
        return 'PROD'
    elif 'QA' in file_name:
        return 'QA'
    else:
        return 'UNKNOWN'

# Function to identify the ID column
def find_id_column(df):
    for col in df.columns:
        if "Id" in col or "ID" in col:  # Case-insensitive check
            return col
    return None  # Return None instead of raising an exception

# Function to compare two CSV files
def compare_csv_files(file_path_1, file_path_2, acronym1, acronym2):
    df1 = pd.read_csv(file_path_1, header=4)
    df2 = pd.read_csv(file_path_2, header=4)

    id_col1 = find_id_column(df1)
    id_col2 = find_id_column(df2)

    if not id_col1 or not id_col2:
        raise ValueError("One or both CSV files are missing an 'Id' column")

    df1.set_index(id_col1, inplace=True)
    df2.set_index(id_col2, inplace=True)

    df1_aligned, df2_aligned = df1.align(df2, join='outer', axis=0, fill_value='')

    diff_mask = df1_aligned != df2_aligned
    diff_df = df1_aligned[diff_mask].combine_first(df2_aligned[diff_mask])

    combined_values = []
    different_ids = []
    for i in range(len(diff_df)):
        row_combined = []
        for col in diff_df.columns:
            if pd.isna(df1_aligned.iloc[i][col]) and not pd.isna(df2_aligned.iloc[i][col]):
                row_combined.append(f' / {acronym2}: {df2_aligned.iloc[i][col]}')
                different_ids.append(diff_df.index[i])
            elif not pd.isna(df1_aligned.iloc[i][col]) and pd.isna(df2_aligned.iloc[i][col]):
                row_combined.append(f'{acronym1}: {df1_aligned.iloc[i][col]} / ')
                different_ids.append(diff_df.index[i])
            elif not pd.isna(df1_aligned.iloc[i][col]) and not pd.isna(df2_aligned.iloc[i][col]) and (df1_aligned.iloc[i][col] != df2_aligned.iloc[i][col]):
                row_combined.append(f'{acronym1}: {df1_aligned.iloc[i][col]} / {acronym2}: {df2_aligned.iloc[i][col]}')
                different_ids.append(diff_df.index[i])
            else:
                row_combined.append('')

        combined_values.append(row_combined)

    combined_values_df = pd.DataFrame(combined_values, columns=diff_df.columns, index=diff_df.index)
    combined_values_df.reset_index(inplace=True)

    # Extract descriptions only for items with differences
    descriptions = {}
    if 'Description' in df1.columns:
        different_ids = list(set(different_ids))  # Remove duplicates
        valid_ids = [id for id in different_ids if id in df1.index]
        descriptions = df1.loc[valid_ids, 'Description'].to_dict()
    else:
        st.write("No 'Description' column found in the first file.")

    return combined_values_df, descriptions

# Function to filter out empty rows
def filter_empty_rows(df):
    # Filter out rows where all values except the index are empty strings or NaNs
    non_empty_rows = df[df.apply(lambda row: row.drop(labels=[df.columns[0]]).replace('', pd.NA).dropna().any(), axis=1)]
    return non_empty_rows

# Function to load parameter descriptions
def load_parameter_descriptions(file):
    param_df = pd.read_csv(file, sep='\t')
    return param_df

# Load parameter descriptions
param_file = 'parameter list.txt'
param_df = load_parameter_descriptions(param_file)

# Streamlit UI
def main():
    st.title('CSV File Comparison Tool')

    uploaded_file1 = st.file_uploader("Choose the first CSV file", type="csv")
    uploaded_file2 = st.file_uploader("Choose the second CSV file", type="csv")

    if uploaded_file1 is not None and uploaded_file2 is not None:
        try:
            acronym1 = extract_acronym(uploaded_file1.name)
            acronym2 = extract_acronym(uploaded_file2.name)
            
            with st.spinner('Processing...'):
                result_df, descriptions = compare_csv_files(uploaded_file1, uploaded_file2, acronym1, acronym2)
                st.write("Before filtering:")
                st.dataframe(result_df)  # Display before filtering for debugging
                result_df = filter_empty_rows(result_df)
                st.success('Comparison complete!')
                st.write("After filtering:")
                st.dataframe(result_df)  # Display after filtering for debugging

                # Display descriptions only for items with differences
                st.subheader("Descriptions for Configuration Items with Differences")
                if descriptions:
                    # Convert the dictionary to a sorted list of tuples
                    sorted_descriptions = sorted((id, desc) for id, desc in descriptions.items() if pd.notna(id) and pd.notna(desc))
                    for id, desc in sorted_descriptions:
                        st.write(f"ID: {id}, Description: {desc}")
                else:
                    st.write("No descriptions found for the configuration items with differences.")

                st.download_button(
                    label="Download CSV",
                    data=result_df.to_csv(index=False).encode('utf-8'),
                    file_name='differences_combined_values.csv',
                    mime='text/csv',
                )
        except ValueError as e:
            st.error(f"Error: {str(e)}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")

    # Display parameter descriptions with hover functionality
    st.write("Parameter Descriptions")
    for index, row in param_df.iterrows():
        st.markdown(f"""
        <div class="tooltip">{row['Pref Name']}
            <span class="tooltiptext">{row['Description']}</span>
        </div>
        """, unsafe_allow_html=True)

    # CSS for tooltip
    st.markdown("""
    <style>
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: pointer;
    }

    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #555;
        color: #fff;
        text-align: center;
        border-radius: 5px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
    }

    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
