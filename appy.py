import streamlit as st
import pandas as pd
import io
import re
from collections import Counter

st.set_page_config(page_title="Missing/Duplicate Checker", page_icon="📊")
st.title("📊 Missing Numbers and Duplicate Checker")
st.markdown("**Developed by: Dr. Anjaneya Reddy, Deputy Librarian, IIMB, Bengaluru**")
st.markdown("**Follow me on** [GitHub](https://github.com/nmanjaneyareddy)")
st.markdown("🛠️ **Key Features:**")
st.markdown("✅ Upload an Excel file with your accession numbers")
st.markdown("✅ Instantly detect missing and duplicate numbers")
st.markdown("✅ Prefix detection and category-wise missing-number report")
st.markdown("✅ Leading zero preservation")
st.markdown("✅ Download a detailed Excel report")

st.write(
    "**NOTE:** Upload an **Excel file (.xlsx)** with data accession numbers/barcode numbers "
    "in **Sheet1** in the **first column** to check for missing and duplicate numbers."
)

uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])


def extract_accession(value):
    """Return prefix, numeric integer, numeric text, and normalized value."""
    if pd.isna(value):
        return None

    value_text = str(value).strip()

    # Handle Excel cells read as floats, e.g. 123.0
    if re.fullmatch(r"\d+\.0", value_text):
        value_text = value_text[:-2]

    match = re.fullmatch(r"([^0-9]*)(\d+)(.*)", value_text)
    if not match:
        return None

    prefix, number_text, suffix = match.groups()

    # Ignore values where text appears after the number, because the original app supports prefix + number only.
    if suffix.strip():
        return None

    normalized = prefix + number_text
    return {
        "prefix": prefix,
        "number": int(number_text),
        "number_text": number_text,
        "normalized": normalized,
    }


def process_file(file):
    try:
        data = pd.read_excel(file, sheet_name="Sheet1", header=None, usecols=[0], dtype=str)
        parsed_rows = data[0].map(extract_accession).dropna().tolist()

        if not parsed_rows:
            st.warning("No valid accession numbers were found in the first column of Sheet1.")
            return pd.DataFrame(), {}, 0

        categorized_numbers = {}
        for row in parsed_rows:
            categorized_numbers.setdefault(row["prefix"], []).append(row)

        results = {}
        output_data = []
        total_missing_count = 0

        for prefix, rows in categorized_numbers.items():
            normalized_values = [row["normalized"] for row in rows]
            numeric_values = [row["number"] for row in rows]
            number_width = max(len(row["number_text"]) for row in rows)

            duplicate_counts = Counter(normalized_values)
            duplicates = sorted([value for value, count in duplicate_counts.items() if count > 1])

            start_number = min(numeric_values)
            end_number = max(numeric_values)
            existing_numbers = set(numeric_values)
            missing_numbers = [num for num in range(start_number, end_number + 1) if num not in existing_numbers]
            formatted_missing = [prefix + str(num).zfill(number_width) for num in missing_numbers]

            total_missing_count += len(missing_numbers)

            results[prefix] = {
                "Missing Numbers": formatted_missing,
                "Duplicates": duplicates,
                "Given Range": (prefix + str(start_number).zfill(number_width), prefix + str(end_number).zfill(number_width)),
                "Missing Count": len(missing_numbers),
            }

            for missing_value in formatted_missing:
                output_data.append([
                    prefix if prefix else "No Prefix",
                    prefix + str(start_number).zfill(number_width),
                    prefix + str(end_number).zfill(number_width),
                    missing_value,
                    "Missing",
                ])

            for duplicate_value in duplicates:
                output_data.append([
                    prefix if prefix else "No Prefix",
                    prefix + str(start_number).zfill(number_width),
                    prefix + str(end_number).zfill(number_width),
                    duplicate_value,
                    "Duplicate",
                ])

        output_df = pd.DataFrame(output_data, columns=["Category", "Start Number", "End Number", "Number", "Status"])
        return output_df, results, total_missing_count

    except ValueError as exc:
        st.error("Could not read Sheet1 first column. Please check that the file contains a sheet named Sheet1.")
        st.exception(exc)
        return None, None, 0
    except Exception as exc:
        st.error("Error processing file.")
        st.exception(exc)
        return None, None, 0


if uploaded_file:
    output_df, results, total_missing = process_file(uploaded_file)

    if output_df is not None:
        st.success("✅ File processed successfully!")
        st.write("### Report")

        for prefix, res in results.items():
            category_name = prefix if prefix else "No Prefix"
            st.subheader("Category: " + category_name)
            st.write("📏 **Given Range:** " + str(res["Given Range"]))
            st.write("🔢 **Missing Numbers:** " + (", ".join(res["Missing Numbers"]) if res["Missing Numbers"] else "None"))
            st.write("🔁 **Duplicates:** " + (", ".join(res["Duplicates"]) if res["Duplicates"] else "None"))
            st.write("❗ **Total Missing in " + category_name + ": " + str(res["Missing Count"]) + "**")

        st.markdown("### 📊 **Total Missing Numbers: " + str(total_missing) + "**")

        if not output_df.empty:
            st.dataframe(output_df, use_container_width=True)

        buffer = io.BytesIO()
        output_df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)

        st.download_button(
            label="📥 Download Report as Excel",
            data=buffer,
            file_name="missing_numbers_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

st.markdown("")
st.markdown("")
st.markdown("---")
st.markdown("**Acknowledgements:**")
st.markdown(
    "I sincerely acknowledge **Dr. Shamprasad M. Pujar**, Chief Librarian, IGIDR, Mumbai, "
    "and **Dr. Prakash I.N.**, Librarian, Alliance University, Bengaluru, for their valuable inputs/suggestions."
)
st.markdown("---")
st.markdown("**If you encounter any issues** with the app, please write to me at: areddy.ragini@gmail.com")
