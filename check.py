import pandas as pd

df = pd.read_excel("slr_screened_complete.xlsx")
# Check for any remaining failures
failed = df[df['Included/Excluded'].astype(str) == '0']
real_failures = failed[failed['Insights'].astype(str).str.contains("Failed after trying all keys")]

if len(real_failures) > 0:
    print(f"⚠️ You have {len(real_failures)} rows that are still broken.")
    print("Since you have a duplicate that SUCCEEDED, you can safely delete these rows.")
else:
    print("✅ All clear! No broken rows found.")