import os
from pypdf import PdfWriter, PdfReader
from src.utils import load_settings

def main():
    print("--- Generating Verification PDF (First 10 Files) ---")

    # 1. Load Settings to find the correct folder
    try:
        settings = load_settings()
        input_folder = settings.get("input_folder", "data/raw_pdfs")
    except:
        # Fallback if config fails
        input_folder = "data/raw_pdfs"
    
    print(f"Reading from: {input_folder}")

    # 2. Find PDFs (Same logic as main script)
    pdf_files = []
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    
    # 3. Take Top 10
    limit = 10
    target_files = pdf_files[:limit]
    
    if not target_files:
        print("No PDFs found!")
        return

    # 4. Create Merged PDF
    writer = PdfWriter()
    output_filename = "Verification_Batch.pdf"

    print("\n" + "="*60)
    print(f"{'Page #':<8} | {'Original Filename'}")
    print("="*60)

    for i, filepath in enumerate(target_files):
        filename = os.path.basename(filepath)
        try:
            reader = PdfReader(filepath)
            if len(reader.pages) > 0:
                # Add the first page to our verification file
                writer.add_page(reader.pages[0])
                print(f"{i+1:<8} | {filename}")
            else:
                print(f"{i+1:<8} | [SKIPPED - Empty PDF] {filename}")
        except Exception as e:
            print(f"{i+1:<8} | [ERROR reading PDF] {filename}")

    # 5. Save
    with open(output_filename, "wb") as out_file:
        writer.write(out_file)

    print("="*60)
    print(f"\nSUCCESS! Created '{output_filename}'")
    print("Open this file to manually check the Titles/Abstracts against your Excel rows.")

if __name__ == "__main__":
    main()