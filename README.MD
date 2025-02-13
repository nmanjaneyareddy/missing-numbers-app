**Missing Numbers and Duplicate Checker**

🛠️ **Overview**
This application helps you identify missing and duplicate numbers from an uploaded Excel file. The application is designed to process accession numbers or barcode numbers with or without prefixes.

🚀 **Features**
Upload an Excel file with data in 'Sheet1' and numbers in the first column.
Automatically identifies missing and duplicate numbers.
Supports prefix-based categorization.
Displays start and end range, missing count, and total missing numbers.
Provides an option to download the report in Excel format.
Handles numbers with leading zeros.


📂 **Input File Requirements**
The uploaded file should be in Excel (.xlsx) format.
The first column in 'Sheet1' should contain the numbers to be checked.


🔢 **Number Format Guidelines**
The app supports both numeric and alphanumeric numbers with prefixes.
Prefixes are automatically detected (e.g., ABC001, XYZ1001).
Leading zeros are preserved.


🛠️ **Usage Instructions**
Open the app by running streamlit run app.py.
Upload your Excel file in the designated upload section.
The app will process the file and display:
Missing numbers (with leading zeros if applicable).
Duplicate entries.
Start and end of the given range.
Missing count per category.
Total missing numbers across all categories.
