import streamlit as st
import pandas as pd
import io
import re
import streamlit as st
import pandas as pd
import io
import re
from collections import Counter

st.set_page_config(
    page_title="Missing / Duplicate Checker",
    page_icon="📚",
    layout="wide"
)

st.title("📊 Missing Numbers and Duplicate Checker")

st.markdown(
    "**Developed by: Dr. Anjaneya Reddy, Deputy Librarian, IIM Bangalore**"
)

st.markdown(
    "**Follow me on:** https://github.com/nmanjaneyareddy"
)

st.markdown("### 🛠 Key Features")

st.markdown("""
✅ Upload Excel (.xlsx)

✅ Detect Missing Numbers

✅ Detect Duplicate Numbers

✅ Automatic Prefix Detection

✅ Preserves Leading Zeros

✅ Download Excel Report

✅ Handles Large Files (5–10 lakh records)
""")

st.info(
    "Upload an Excel (.xlsx) file with accession/barcode numbers "
    "in Sheet1 and First Column."
)

uploaded_file = st.file_uploader(
    "Choose Excel File",
    type=["xlsx"]
)


###########################################################
# Function
###########################################################

def extract_numbers_with_prefix(value):

    if pd.isna(value):
        return None

    value = str(value).strip()

    match = re.match(r'([A-Za-z&`-]*)(\d+)', value)

    if match:
        prefix, number = match.groups()
        return prefix + number.zfill(len(number))

    return None


###########################################################
# Processing
###########################################################

def process_file(file):

    try:

        data = pd.read_excel(
            file,
            sheet_name="Sheet1",
            header=None,
            usecols=[0],
            dtype=str
        )

        scanned_numbers = (
            data[0]
            .map(extract_numbers_with_prefix)
            .dropna()
            .tolist()
        )

        categorized_numbers = {}

        for item in scanned_numbers:

            m = re.match(r'([A-Za-z&`-]*)(\d+)', item)

            prefix = m.group(1) if m else ""

            categorized_numbers.setdefault(prefix, []).append(item)

        results = {}

        output_rows = []

        total_missing = 0

        for prefix, numbers in categorized_numbers.items():

            counter = Counter(numbers)

            duplicates = sorted(
                [k for k, v in counter.items() if v > 1]
            )

            numeric_values = []

            for x in numbers:

                m = re.search(r'\d+', x)

                if m:
                    numeric_values.append(int(m.group()))

            numeric_values = sorted(set(numeric_values))

            if len(numeric_values) == 0:
                continue

            start_number = numeric_values[0]
            end_number = numeric_values[-1]

            existing = set(numeric_values)

            missing_numbers = [
                i for i in range(start_number, end_number + 1)
                if i not in existing
            ]

            total_missing += len(missing_numbers)

            number_length = len(
                re.search(r'\d+', numbers[0]).group()
            )

            missing_formatted = [
                prefix + str(i).zfill(number_length)
                for i in missing_numbers
            ]

            results[prefix] = {
                "Range": (start_number, end_number),
                "Missing": missing_formatted,
                "Duplicates": duplicates,
                "Missing Count": len(missing_formatted),
                "Duplicate Count": len(duplicates)
            }

            for item in missing_formatted:
                output_rows.append([
                    prefix,
                    start_number,
                    end_number,
                    item,
                    "Missing"
                ])

            for item in duplicates:
                output_rows.append([
                    prefix,
                    start_number,
                    end_number,
                    item,
                    "Duplicate"
                ])

        output_df = pd.DataFrame(
            output_rows,
            columns=[
                "Category",
                "Start Number",
                "End Number",
                "Number",
                "Status"
            ]
        )

        return output_df, results, total_missing

    except Exception as e:
        st.error(e)
        return None, None, 0


###########################################################
# Main
###########################################################

if uploaded_file:

    with st.spinner("Processing..."):

        output_df, results, total_missing = process_file(uploaded_file)

    if output_df is not None:

        st.success("✅ Processing Completed")

        st.metric(
            "Total Missing Numbers",
            total_missing
        )

        for prefix, res in results.items():

            st.markdown("---")

            st.subheader(
                f"Category : {prefix if prefix else 'No Prefix'}"
            )

            st.write(
                f"📏 Range : {res['Range'][0]} - {res['Range'][1]}"
            )

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Missing",
                    res["Missing Count"]
                )

            with col2:
                st.metric(
                    "Duplicates",
                    res["Duplicate Count"]
                )

            if len(res["Missing"]) > 0:

                st.write(
                    "**First 100 Missing Numbers**"
                )

                st.write(
                    ", ".join(res["Missing"][:100])
                )

                with st.expander(
                    "View Complete Missing Numbers"
                ):
                    st.write(res["Missing"])

            else:

                st.success("No Missing Numbers")

            if len(res["Duplicates"]) > 0:

                st.write(
                    "**Duplicate Numbers**"
                )

                st.write(
                    ", ".join(res["Duplicates"][:100])
                )

                with st.expander(
                    "View Complete Duplicate Numbers"
                ):
                    st.write(res["Duplicates"])

            else:

                st.success("No Duplicate Numbers")

        #######################################################
        # Download
        #######################################################

        buffer = io.BytesIO()

        with pd.ExcelWriter(
            buffer,
            engine="openpyxl"
        ) as writer:

            output_df.to_excel(
                writer,
                index=False,
                sheet_name="Report"
            )

        buffer.seek(0)

        st.download_button(
            "📥 Download Excel Report",
            data=buffer,
            file_name="Missing_Duplicate_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

###########################################################
# Footer
###########################################################

st.markdown("---")

st.markdown("### Acknowledgements")

st.markdown("""
I sincerely acknowledge

**Dr. Shamprasad M. Pujar**

Chief Librarian, IGIDR Mumbai

and

**Dr. Prakash I.N.**

Librarian, Alliance University

for their valuable suggestions and encouragement.
""")

st.markdown("---")

st.markdown(
    "**For support:** areddy@iimb.ac.in"
)
