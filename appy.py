import streamlit as st
import pandas as pd
import io
import re


st.title("📊 Missing Numbers and Duplicate Checker")
st.markdown("**Developed by: Dr. Anjaneya Reddy, IGIDR, Mumbai**")
st.markdown("Follow me on [GitHub](https://github.com/nmanjaneyareddy)")

st.write("Upload an **Excel file (.xlsx)** with data (accession numbers/barcode numbers) in **'Sheet1'** in the **First column** to check for missing and duplicate numbers.")

uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

def extract_numbers_with_prefix(value):
    if isinstance(value, (int, float)):
        return str(int(value)) if not pd.isna(value) else None
    elif isinstance(value, str):
        match = re.match(r'(\D*)(\d+)', value)
        if match:
            prefix, number = match.groups()
            return f"{prefix}{number.zfill(len(number))}"  # Preserve leading zeros
    return None

def process_file(file):
    try:
        data = pd.read_excel(file, sheet_name='Sheet1', header=None, usecols=[0])
        scanned_numbers = data[0].map(extract_numbers_with_prefix).dropna().tolist()

        categorized_numbers = {}
        total_missing_count = 0  # ✅ Track total missing numbers
        output_data = []

        for num in scanned_numbers:
            match = re.match(r'(\D*)(\d+)', num)
            prefix = match.group(1) if match else "No Prefix"
            categorized_numbers.setdefault(prefix, []).append(num)

        results = {}

        for prefix, numbers in categorized_numbers.items():
            duplicates = sorted(set(x for x in numbers if numbers.count(x) > 1))
            numeric_values = sorted(set(int(re.search(r'\d+', x).group()) for x in numbers if re.search(r'\d+', x)))

            start_number, end_number = numeric_values[0], numeric_values[-1]
            total_range = set(range(start_number, end_number + 1))
            missing_numbers = sorted(total_range - set(numeric_values))

            # ✅ Add to total missing count
            total_missing_count += len(missing_numbers)

            # Preserve leading zeros based on the length of the first number
            num_length = len(re.search(r'\d+', numbers[0]).group()) if numbers else 0

            results[prefix] = {
                "Missing Numbers": [f"{prefix}{str(mn).zfill(num_length)}" for mn in missing_numbers],
                "Duplicates": duplicates,
                "Given Range": (start_number, end_number),  # ✅ Add Given Range
                "Missing Count": len(missing_numbers)       # ✅ Add Missing Count for each category
            }

            for mn in missing_numbers:
                output_data.append([prefix, start_number, end_number, f"{prefix}{str(mn).zfill(num_length)}", "Missing"])
            for dn in duplicates:
                output_data.append([prefix, start_number, end_number, dn, "Duplicate"])

        output_df = pd.DataFrame(output_data, columns=["Category", "Start Number", "End Number", "Number", "Status"])

        return output_df, results, total_missing_count  # ✅ Return total missing count
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None, None, 0

if uploaded_file:
    output_df, results, total_missing = process_file(uploaded_file)

    if output_df is not None:
        st.success("✅ File processed successfully!")
        st.write("### Report")

        for prefix, res in results.items():
            st.subheader(f"Category: {prefix if prefix else 'No Prefix'}")
            st.write(f"📏 **Given Range:** {res['Given Range']}")  # ✅ Display Given Range
            st.write(f"🔢 Missing Numbers: {', '.join(res['Missing Numbers']) if res['Missing Numbers'] else 'None'}")
            st.write(f"🔁 Duplicates: {', '.join(res['Duplicates']) if res['Duplicates'] else 'None'}")
            st.write(f"❗ **Total Missing in {prefix if prefix else 'No Prefix'}: {res['Missing Count']}**")  # ✅ Display Missing Count per Category

        # ✅ Display the total missing count
        st.markdown(f"### 📊 **Total Missing Numbers: {total_missing}**")

        # Download button with buffer
        buffer = io.BytesIO()
        output_df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)

        st.download_button(
            label="📥 Download Report as Excel",
            data=buffer,
            file_name="missing_numbers_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )



# ✅ Footer Section
st.markdown("")
st.markdown("")
st.markdown("")
st.markdown("**Acknowledgements:**")
st.markdown("I sincerely acknowledge Dr. Shamprasad M. Pujar, Chief Librarian, IGIDR, Mumbai, and Dr. Prakash I.N., Librarian, Alliance University, Bengaluru, for their valuable inputs/suggestions.")
