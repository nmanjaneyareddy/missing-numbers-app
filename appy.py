import streamlit as st
import pandas as pd
import io
import re

# Title
st.title("📊 Missing Numbers and Duplicate Checker")

# Instructions
st.write("Upload an Excel file (.xlsx) with data in 'Sheet1' to check for missing and duplicate numbers.")

# File uploader
uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

def extract_numbers_with_prefix(value):
    if isinstance(value, (int, float)):
        return str(int(value)) if not pd.isna(value) else None
    elif isinstance(value, str):
        match = re.match(r'(\D*)(\d+)', value)
        if match:
            prefix, number = match.groups()
            return f"{prefix}{int(number)}"
    return None

def process_file(file):
    try:
        data = pd.read_excel(file, sheet_name='Sheet1', header=None, usecols=[0])
        scanned_numbers = data[0].map(extract_numbers_with_prefix).dropna().tolist()

        categorized_numbers = {}
        for num in scanned_numbers:
            match = re.match(r'(\D*)(\d+)', num)
            prefix = match.group(1) if match else "No Prefix"
            categorized_numbers.setdefault(prefix, []).append(num)

        results = {}
        output_data = []

        for prefix, numbers in categorized_numbers.items():
            duplicates = sorted(set(x for x in numbers if numbers.count(x) > 1))
            numeric_values = sorted(set(int(re.search(r'\d+', x).group()) for x in numbers if re.search(r'\d+', x)))

            start_number, end_number = numeric_values[0], numeric_values[-1]
            total_range = set(range(start_number, end_number + 1))
            missing_numbers = sorted(total_range - set(numeric_values))

            results[prefix] = {
                "Missing Numbers": [f"{prefix}{mn}" for mn in missing_numbers],
                "Duplicates": duplicates
            }

            for mn in missing_numbers:
                output_data.append([prefix, start_number, end_number, f"{prefix}{mn}", "Missing"])
            for dn in duplicates:
                output_data.append([prefix, start_number, end_number, dn, "Duplicate"])

        output_df = pd.DataFrame(output_data, columns=["Category", "Start Number", "End Number", "Number", "Status"])

        return output_df, results
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None, None

if uploaded_file:
    output_df, results = process_file(uploaded_file)

    if output_df is not None:
        st.success("✅ File processed successfully!")
        st.write("### Results")

        for prefix, res in results.items():
            st.subheader(f"Category: {prefix if prefix else 'No Prefix'}")
            st.write(f"🔢 Missing Numbers: {', '.join(res['Missing Numbers']) if res['Missing Numbers'] else 'None'}")
            st.write(f"🔁 Duplicates: {', '.join(res['Duplicates']) if res['Duplicates'] else 'None'}")

        st.download_button(
            label="📥 Download Report as Excel",
            data=output_df.to_excel(index=False),
            file_name="missing_numbers_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
