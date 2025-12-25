import os
import time
import pandas as pd
from tqdm import tqdm
from src.utils import load_settings, load_criteria, ensure_directories
from src.pdf_utils import extract_text_from_pdf
from src.metadata import extract_metadata
from src.ai_engine import AIEngine
from src.logger import setup_logger

# Initialize Logger
logger = setup_logger()

# --- SETTINGS ---
TEST_LIMIT = None  # None = Run Everything

def main():
    logger.info("--- Auto-SLR-Screener Started (Professional Logging Mode) ---")
    
    try:
        settings = load_settings()
        inc_list, exc_list = load_criteria() 
        ensure_directories(settings)
        ai = AIEngine()
    except Exception as e:
        logger.critical(f"Startup Failed: {e}")
        return

    input_folder = settings.get("input_folder", "data/raw_pdfs")
    logger.info(f"Scanning folder: {input_folder}")
    
    pdf_files = []
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    
    if TEST_LIMIT:
        pdf_files = pdf_files[:TEST_LIMIT]
        logger.warning(f"⚠️ TEST MODE ACTIVE: Processing subset of {len(pdf_files)} files.")
    else:
        logger.info(f"Found {len(pdf_files)} PDFs to process.")

    output_file = settings.get("output_file")
    results = []
    processed_files = set()

    if os.path.exists(output_file):
        try:
            existing = pd.read_excel(output_file)
            results = existing.to_dict('records')
            if 'File Name' in existing.columns:
                processed_files = set(existing['File Name'].astype(str))
            logger.info(f"Resuming... {len(processed_files)} papers already completed.")
        except:
            logger.warning("Output file exists but unreadable. Starting fresh.")

    # Main Loop
    for i, filepath in tqdm(enumerate(pdf_files), total=len(pdf_files)):
        meta = extract_metadata(filepath)
        
        if meta["File Name"] in processed_files:
            continue

        text = extract_text_from_pdf(filepath, settings.get("pdf_char_limit", 3500))
        
        if len(text) < 50:
            logger.warning(f"Skipping Empty PDF: {meta['File Name']}")
            meta["Research Paper Title"] = "Unreadable PDF"
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

            # 1. Extract Flags
            inc_score = 0
            inc_data = response.get("Inclusion_Breakdown", {})
            for idx, c in enumerate(inc_list): 
                val = 1 if inc_data.get(f"Inc_{idx+1}", 0) == 1 else 0
                meta[c] = val
                inc_score += val

            exc_score = 0
            exc_data = response.get("Exclusion_Breakdown", {})
            for idx, c in enumerate(exc_list): 
                val = 1 if exc_data.get(f"Exc_{idx+1}", 0) == 1 else 0
                meta[c] = val
                exc_score += val

            # 2. Strict Logic Decision
            if exc_score > 0:
                meta["Included/Excluded"] = 0
                logger.debug(f"➖ Excluded (Criteria Hit): {meta['File Name']}")
            elif inc_score == 0:
                meta["Included/Excluded"] = 0
                logger.debug(f"➖ Excluded (No Match): {meta['File Name']}")
            else:
                meta["Included/Excluded"] = 1
                logger.info(f"➕ INCLUDED: {meta['File Name']}")

            # 3. Metadata
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
            logger.error(f"Analysis Failed: {meta['File Name']}")

        results.append(meta)

        if (i + 1) % 5 == 0:
            save_excel(results, output_file, inc_list, exc_list)
            logger.info(f"💾 Saved Progress ({i+1}/{len(pdf_files)})")
        
        time.sleep(settings.get("sleep_seconds", 20))

    save_excel(results, output_file, inc_list, exc_list)
    logger.info("--- BATCH COMPLETE ---")

def save_excel(results, output_file, inc_list, exc_list):
    df = pd.DataFrame(results)
    base_cols = ['Category', 'Database', 'Year', 'Research Paper Title', 'Included/Excluded']
    criteria_cols = inc_list + exc_list
    meta_cols = [
        'Review/Research Paper', 'Publication', 'Journal/Conference Paper',
        'Scopus/SCI/SCIE/specific conference paper', 'First Author Name',
        'First Author’s Country Name', 'Study Area Country Name', 'Insights', 'File Name'
    ]
    final_order = [c for c in base_cols + criteria_cols + meta_cols if c in df.columns]
    df[final_order].to_excel(output_file, index=False)

if __name__ == "__main__":
    main()