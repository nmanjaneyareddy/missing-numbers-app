import streamlit as st
import pandas as pd
import io
import re
from collections import Counter

# --- CRITICAL PERFORMANCE NOTE ---
# This code requires the 'python-calamine' library for lightning-fast Excel parsing.
# If running locally, run: pip install python-calamine
# If deploying to Streamlit Cloud, add 'python-calamine' to your requirements.txt file.

st.set_page_config(page_title="Missing/Duplicate Checker", page_icon="📊", layout="wide")
st.title("📊 High-Performance Missing & Duplicate Checker")
st.markdown("**Developed by: Dr. Anjaneya Reddy, Deputy Librarian, IIMB, Bengaluru**")
st.markdown("⚡ *Optimized to comfortably handle 2,00,000+ rows.*")

uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

def extract_numbers_with_prefix(value):
    if isinstance(value, (int, float)):
        return str(int(value)) if not pd.isna(value) else None
    elif isinstance(value, str):
        # Strips accidental whitespaces
        value = value.strip()
        match = re.match(r'(\D*)(\d+)', value)
        if match:
            prefix, number = match.groups()
            return f"{prefix}{number}"
    return None

def process_file(file):
    try:
        # 🔥 OPTIMIZATION 1: Use 'calamine' engine (Rust-backed, ultra-low memory usage)
        # We enforce dtype=str initially to completely bypass float conversion bugs
        data = pd.read_excel(file, sheet_name='Sheet1', header=None, usecols=[0], dtype=str, engine='calamine')
        
        # Fast extraction using vectorized operations / mapping
        scanned_numbers = data[0].dropna().map(extract_numbers_with_prefix).dropna().tolist()

        categorized_numbers = {}
        total_missing_count = 0  
        output_summary = []

        # Categorize numbers by prefix
        for num in scanned_numbers:
            match = re.match(r'(\D*)(\d+)', num)
            prefix = match.group(1) if match else "No Prefix"
            categorized_numbers.setdefault(prefix, []).append(num)

        results = {}

        for prefix, numbers in categorized_numbers.items():
            # Fast Duplicate Check O(N)
            counts = Counter(numbers)
            duplicates = sorted([x for x, count in counts.items() if count > 1])
            
            # Extract just numeric values efficiently
            numeric_values = []
            for x in numbers:
                match = re.search(r'\d+', x)
                if match:
                    numeric_values.append(int(match.group()))
            
            if not numeric_values:
                continue
                
            numeric_values = sorted(set(numeric_values))
            start_number, end_number = numeric_values[0], numeric_values[-1]
            
            # Calculate missing values using sets
            total_range = set(range(start_number, end_number + 1))
            missing_numbers_raw = sorted(total_range - set(numeric_values))
            
            # Track total count
            missing_count = len(missing_numbers_raw)
            total_missing_count += missing_count

            # Determine leading zero length formatting dynamically
            first_digits_match = re.search(r'\d+', numbers[0])
            num_length = len(first_digits_match.group()) if first_digits_match else 0

            # Re-format missing numbers with original formatting
            missing_numbers_formatted = [f"{prefix}{str(mn).zfill(num_length)}" for mn in missing_numbers_raw]
            
            results[prefix] = {
                "Missing Numbers": missing_numbers_formatted,
                "Duplicates": duplicates,
                "Given Range": (f"{prefix}{str(start_number).zfill(num_length)}", f"{prefix}{str(end_number).zfill(num_length)}"),  
                "Missing Count": missing_count       
            }

            # 🔥 OPTIMIZATION 2: Aggregated Summary Generation (Prevents RAM crashes from gigantic list generation)
            # Log Duplicates
            for dn in duplicates:
                output_summary.append([prefix, results[prefix]["Given Range"][0], results[prefix]["Given Range"][1], dn, "Duplicate"])
            
            # Log Missing Ranges compactly if too many, or individually if small
            if missing_count > 5000:
                output_summary.append([prefix, results[prefix]["Given Range"][0], results[prefix]["Given Range"][1], f"Too many to list individually ({missing_count} total). See UI display or check range limits.", "Missing Batch Summary"])
            else:
                for mn in missing_numbers_formatted:
                    output_summary.append([prefix, results[prefix]["Given Range"][0], results[prefix]["Given Range"][1], mn, "Missing"])

        output_df = pd.DataFrame(output_summary, columns=["Category", "Start Range", "End Range", "Identified Number", "Status"])
        return output_df, results, total_missing_count  

    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None, None, 0

if uploaded_file:
    with st.spinner("Processing large dataset... please hold on..."):
        output_df, results, total_missing = process_file(uploaded_file)

    if output_df is not None:
        st.success("✅ File processed cleanly!")
        
        # Metrics Display
        st.metric(label="📊 Total Missing Numbers across all Categories", value=f"{total_missing:,}")

        st.write("### 📋 Category breakdown Report")
        for prefix, res in results.items():
            with st.expander(f"Category: {prefix if prefix else 'No Prefix'} ({res['Missing Count']:,} Missing)", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"📏 **Given Operational Range:** `{res['Given Range'][0]}` to `{res['Given Range'][1]}`")
                    st.write(f"❗ **Missing Count in this Category:** `{res['Missing Count']:,}`")
                
                with col2:
                    # 🔥 OPTIMIZATION 3: Safety UI truncation so the browser tab doesn't freeze up
                    if res['Missing Numbers']:
                        preview_limit = 200
                        missing_text = ', '.join(res['Missing Numbers'][:preview_limit])
                        if len(res['Missing Numbers']) > preview_limit:
                            missing_text += f"... and {len(res['Missing Numbers']) - preview_limit:,} more numbers."
                        st.write(f"🔢 **Missing Numbers (Preview):** {missing_text}")
                    else:
                        st.write("🔢 **Missing Numbers:** None 🎉")

                    st.write(f"🔁 **Duplicates:** {', '.join(res['Duplicates']) if res['Duplicates'] else 'None'}")

        # Download setup
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            output_df.to_excel(writer, index=False, sheet_name="Data Diagnostics")
        buffer.seek(0)

        st.download_button(
            label="📥 Download Structured Diagnostics Report",
            data=buffer,
            file_name="comprehensive_missing_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ✅ Footer Section
st.markdown("---")
st.markdown("If you continue to experience timeouts on live servers with large logs, drop a note to: areddy@igidr.ac.in")
