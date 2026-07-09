import streamlit as st
import pandas as pd
import io
import re
from collections import Counter

st.set_page_config(page_title="High-Scale CSV Checker", page_icon="📊", layout="wide")
st.title("📊 Ultra-Scale Missing & Duplicate Checker (300k+ Rows)")
st.markdown("**Developed by: Dr. Anjaneya Reddy, Deputy Librarian, IIMB, Bengaluru**")

# Update instructions for the user
st.info("💡 **For 3,00,000+ rows:** Please save your Excel file as a **CSV (.csv)** file before uploading. This bypasses the memory limits of cloud servers.")

uploaded_file = st.file_uploader("Choose your converted CSV file", type=["csv"])

def extract_numbers_with_prefix(value):
    if pd.isna(value):
        return None
    val_str = str(value).strip()
    if not val_str or val_str.lower() == 'nan':
        return None
    match = re.match(r'(\D*)(\d+)', val_str)
    if match:
        return match.groups() # Returns (prefix, number_string)
    return None

def process_mega_csv(file):
    try:
        # Memory tracking & optimization structures
        categorized_ints = {}
        categorized_strings = {}
        prefix_zero_lens = {}
        
        # Read file in small memory chunks (10,000 rows at a time)
        # We specify header=None and usecols=[0] to only look at the first column
        for chunk in pd.read_csv(file, header=None, usecols=[0], chunksize=10000, dtype=str):
            for item in chunk[0]:
                parsed = extract_numbers_with_prefix(item)
                if parsed:
                    prefix, num_str = parsed
                    
                    # Store original values for duplicate tracking
                    categorized_strings.setdefault(prefix, []).append(f"{prefix}{num_str}")
                    
                    # Store pure integers for range/missing mathematical logic
                    categorized_ints.setdefault(prefix, []).append(int(num_str))
                    
                    # Track leading zero format template lengths dynamically
                    if prefix not in prefix_zero_lens:
                        prefix_zero_lens[prefix] = len(num_str)

        if not categorized_ints:
            return None, {}, 0

        total_missing_count = 0
        results = {}
        output_summary = []

        # Process statistics for each localized prefix block
        for prefix, int_list in categorized_ints.items():
            str_list = categorized_strings[prefix]
            num_length = prefix_zero_lens.get(prefix, 0)
            
            # 1. Lightning Fast Duplicates O(N)
            counts = Counter(str_list)
            duplicates = sorted([x for x, count in counts.items() if count > 1])

            # 2. Optimized Range Logic
            unique_ints = sorted(set(int_list))
            start_num, end_num = unique_ints[0], unique_ints[-1]
            
            # Perform direct mathematical set difference 
            existing_set = set(unique_ints)
            full_range_set = set(range(start_num, end_num + 1))
            missing_ints = sorted(full_range_set - existing_set)
            
            missing_count = len(missing_ints)
            total_missing_count += missing_count

            # Safely build string formats for screen display up to a limit
            missing_formatted = []
            if missing_count <= 10000:
                missing_formatted = [f"{prefix}{str(mn).zfill(num_length)}" for mn in missing_ints]
            else:
                missing_formatted = ["[Large break detected: Download summary report to inspect all numbers]"]

            start_str = f"{prefix}{str(start_num).zfill(num_length)}"
            end_str = f"{prefix}{str(end_num).zfill(num_length)}"

            results[prefix] = {
                "Missing Numbers": missing_formatted,
                "Duplicates": duplicates,
                "Given Range": (start_str, end_str),
                "Missing Count": missing_count,
                "RawMissingInts": missing_ints
            }

            # 3. Add to Download Output Matrix
            for dn in duplicates:
                output_summary.append([prefix, start_str, end_str, dn, "Duplicate"])
            
            if missing_count > 5000:
                output_summary.append([prefix, start_str, end_str, f"Gaps identified: {missing_count:,} missing sequence IDs in this block.", "Missing Block Alert"])
            else:
                for mn in missing_ints:
                    output_summary.append([prefix, start_str, end_str, f"{prefix}{str(mn).zfill(num_length)}", "Missing"])

        output_df = pd.DataFrame(output_summary, columns=["Category", "Start Range", "End Range", "Identified Target", "Status"])
        return output_df, results, total_missing_count

    except Exception as e:
        st.error(f"Stream Error: {e}")
        return None, {}, 0

if uploaded_file:
    with st.spinner("Streaming data chunks safely... keeping memory low..."):
        output_df, results, total_missing = process_mega_csv(uploaded_file)

    if output_df is not None:
        st.success("📊 300k+ Dataset Analyzed Successfully!")
        st.metric(label="Total Missing Items Across Dataset", value=f"{total_missing:,}")

        st.write("### 📂 Structural Breakdown")
        for prefix, res in results.items():
            display_name = prefix if prefix != "" else "No Prefix Columns"
            with st.expander(f"Prefix Block: '{display_name}' ({res['Missing Count']:,} Missing)", expanded=True):
                
                c1, c2 = st.columns(2)
                with c1:
                    st.info(f"📏 **Range Boundaries:** `{res['Given Range'][0]}` to `{res['Given Range'][1]}`")
                    st.error(f"❌ **Missing Total:** {res['Missing Count']:,} items")
                with c2:
                    st.warning(f"🔁 **Duplicates Found:** {len(res['Duplicates']):,}")
                    if res['Duplicates']:
                        st.text(", ".join(res['Duplicates'][:50]) + ("..." if len(res['Duplicates']) > 50 else ""))
                    
                if res['Missing Count'] > 0:
                    st.write("**Missing Sequence Snippet Preview:**")
                    if res['Missing Count'] > 300:
                        st.text(", ".join(res['Missing Numbers'][:300]) + f"... [Truncated view for browser speed. Total missing here: {res['Missing Count']:,}]")
                    else:
                        st.text(", ".join(res['Missing Numbers']))

        # Setup CSV output buffer (CSV is drastically lighter than Excel for writing logs out)
        buffer = io.StringIO()
        output_df.to_csv(buffer, index=False)
        csv_data = buffer.getvalue()

        st.download_button(
            label="📥 Download Diagnostics Report (.csv)",
            data=csv_data,
            file_name="diagnostics_report.csv",
            mime="text/csv"
        )
