import os
import pandas as pd

def normalize_name(name):
    """Cleans filename for accurate comparison."""
    return str(name).strip()

def main():
    print("🚀 Starting Deep Scan of all subfolders...\n")
    
    # 1. Define Paths
    # We start from the current directory and look for 'data'
    base_dir = os.getcwd()
    raw_pdf_dir = os.path.join(base_dir, "data", "raw_pdfs")
    excel_path = os.path.join(base_dir, "data", "results", "slr_screened.xlsx")

    # 2. Recursively find ALL PDFs in the directory tree
    all_pdf_files = set()
    print(f"📂 Scanning: {raw_pdf_dir}")
    
    if not os.path.exists(raw_pdf_dir):
        print(f"❌ Error: Directory not found: {raw_pdf_dir}")
        return

    for root, dirs, files in os.walk(raw_pdf_dir):
        for file in files:
            if file.lower().endswith(".pdf"):
                all_pdf_files.add(normalize_name(file))
                
    print(f"   Found {len(all_pdf_files)} PDFs in total.")

    # 3. Load Processed List from Excel
    print(f"\n📊 Reading Excel: {excel_path}")
    if not os.path.exists(excel_path):
        print("❌ Error: Excel file not found.")
        return

    try:
        df = pd.read_excel(excel_path)
        # Use the 'File Name' column. If it doesn't exist, try 'Research Paper Title' as fallback
        col_name = 'File Name' if 'File Name' in df.columns else 'Research Paper Title'
        
        processed_files = set(df[col_name].apply(normalize_name))
        print(f"   Found {len(processed_files)} rows in Excel.")
        
    except Exception as e:
        print(f"❌ Error reading Excel: {e}")
        return

    # 4. Compare
    missing_files = all_pdf_files - processed_files
    
    print("\n" + "="*40)
    print(f"📄 Total PDFs on Disk:    {len(all_pdf_files)}")
    print(f"✅ Processed in Excel:    {len(processed_files)}")
    print(f"⚠️  Not Processed Yet:     {len(missing_files)}")
    print("="*40)

    # 5. Report
    if missing_files:
        print(f"\n🔍 Found {len(missing_files)} missing papers. Here are the first 10:")
        sorted_missing = sorted(list(missing_files))
        for f in sorted_missing[:10]:
            print(f"   ❌ {f}")
            
        if len(missing_files) > 10:
            print(f"   ...and {len(missing_files)-10} more.")
            
        # Save to file
        with open("missing_files_audit.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(sorted_missing))
        print(f"\n💾 Full list saved to: 'missing_files_audit.txt'")
        
        print("\n💡 ACTION: Run 'python main.py' to process these specific files.")
    else:
        print("\n🎉 COMPLETION CONFIRMED: 100% of files have been processed.")

if __name__ == "__main__":
    main()