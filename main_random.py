import os
import time
import random
import pandas as pd
from tqdm import tqdm
from pypdf import PdfWriter, PdfReader

# Import custom modules
from src.utils import load_settings, load_criteria, ensure_directories
from src.pdf_utils import extract_text_from_pdf
from src.metadata import extract_metadata
from src.ai_engine import AIEngine

# --- CONFIGURATION ---
SAMPLE_SIZE = 20  # Number of random files to test
VERIFICATION_PDF_NAME = "Verification_Random_20.pdf"

def main():
    print(f"--- Auto-SLR-Screener (Random Sample Mode: {SAMPLE_SIZE} Files) ---")
    
    # 1. Setup
    try:
        settings = load_settings()
        inc_list, exc_list = load_criteria() 
        ensure_directories(settings)
        ai = AIEngine()
    except Exception as e:
        print(f"Startup Failed: {e}")
        return

    # 2. Gather All Files
    input_folder = settings.get("input_folder", "data/raw_pdfs")
    print(f"Scanning: {input_folder}")
    
    all_pdf_files = []
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            if file.lower().endswith('.pdf'):
                all_pdf_files.append(os.path.join(root, file))
    
    total_found = len(all_pdf_files)
    print(f"Total PDFs found: {total_found}")

    # 3. Select Random Sample
    if total_found > SAMPLE_SIZE:
        target_files = random.sample(all_pdf_files, SAMPLE_SIZE)
        print(f"🎲 Selected {SAMPLE_SIZE} random files for verification.")
    else:
        target_files = all_pdf_files
        print(f"⚠️ Less than {SAMPLE_SIZE} files found. Processing all {total_found}.")

    # 4. Generate Verification PDF First
    print(f"\nGenering {VERIFICATION_PDF_NAME} for visual check...")
    pdf_writer = PdfWriter()
    valid_files = [] # Only process files we can actually read

    for filepath in target_files:
        try:
            reader = PdfReader(filepath)
            if len(reader.pages) > 0:
                pdf_writer.add_page(reader.pages[0])
                valid_files.append(filepath) # Keep sync between PDF and Excel
            else:
                print(f"Skipping empty PDF: {os.path.basename(filepath)}")
        except Exception as e:
            print(f"Skipping corrupt PDF: {os.path.basename(filepath)}")

    with open(VERIFICATION_PDF_NAME, "wb") as f:
        pdf_writer.write(f)
    print(f"✅ Created {VERIFICATION_PDF_NAME}. Row N in Excel = Page N in this PDF.\n")

    # 5. Process the Valid Files through AI
    output_file = settings.get("output_file")
    results = []

    print("Starting AI Analysis on Sample...")
    for i, filepath in tqdm(enumerate(valid_files), total=len(valid_files)):
        meta = extract_metadata(filepath)
        text = extract_text_from_pdf(filepath, settings.get("pdf_char_limit", 3500))
        
        # Handle unreadable text (even if PDF opened, text layer might be missing)
        if len(text) < 50:
            meta["Research Paper Title"] = "Unreadable Text Layer"
            meta["Included/Excluded"] = 0
            for c in inc_list + exc_list: meta[c] = 0
            results.append(meta)
            continue

        # AI Call
        response = ai.analyze_paper(
            meta["File Name"], text, inc_list, exc_list,
            settings.get("model_id"), settings.get("temperature")
        )

        if response:
            extracted_title = response.get("Extracted_Title", "").strip()
            meta["Research Paper Title"] = extracted_title if len(extracted_title) > 5 else meta["File Name"]

            # --- EXTRACT FLAGS ---
            inc_score = 0
            inc_data = response.get("Inclusion_Breakdown", {})
            for idx, c in enumerate(inc_list): 
                val = inc_data.get(f"Inc_{idx+1}", 0)
                meta[c] = val
                inc_score += val

            exc_score = 0
            exc_data = response.get("Exclusion_Breakdown", {})
            for idx, c in enumerate(exc_list): 
                val = exc_data.get(f"Exc_{idx+1}", 0)
                meta[c] = val
                exc_score += val

            # --- STRICT LOGIC CALCULATION ---
            # Exclude if ANY exclusion criteria is met OR NO inclusion criteria are met
            if exc_score > 0:
                meta["Included/Excluded"] = 0
            elif inc_score == 0:
                meta["Included/Excluded"] = 0
            else:
                meta["Included/Excluded"] = 1

            # --- METADATA ---
            meta["Review/Research Paper"] = response.get("Review_Research_Type", "Research Paper")
            meta["Publication"] = response.get("Publisher", "")
            meta["Journal/Conference Paper"] = response.get("Publication_Type", "Unknown")
            meta["Scopus/SCI/SCIE/specific conference paper"] = response.get("Venue_Name", "") 
            meta["First Author Name"] = response.get("First_Author_Name", "")
            meta["First Author’s Country Name"] = response.get("First_Author_Country", "Unknown")
            meta["Study Area Country Name"] = response.get("Study_Area_Country", "Unknown")
            meta["Insights"] = response.get("Insights", "")
            
        else:
            meta["Included/Excluded"] = "Error"
            meta["Insights"] = "AI API Failed"

        results.append(meta)
        
        # Sleep to respect rate limits
        time.sleep(settings.get("sleep_seconds", 20))

    # 6. Save Final Excel
    df = pd.DataFrame(results)
    
    # Dynamic Column Ordering
    base_cols = ['Category', 'Database', 'Year', 'Research Paper Title', 'Included/Excluded']
    criteria_cols = inc_list + exc_list
    meta_cols = [
        'Review/Research Paper', 'Publication', 'Journal/Conference Paper',
        'Scopus/SCI/SCIE/specific conference paper', 'First Author Name',
        'First Author’s Country Name', 'Study Area Country Name', 'Insights', 'File Name'
    ]
    
    final_order = [c for c in base_cols + criteria_cols + meta_cols if c in df.columns]
    df[final_order].to_excel(output_file, index=False)
    
    print("-" * 60)
    print("RANDOM SAMPLE TEST COMPLETE")
    print(f"1. Visual Check: Open '{VERIFICATION_PDF_NAME}'")
    print(f"2. Data Check:   Open '{output_file}'")
    print("-" * 60)

if __name__ == "__main__":
    main()