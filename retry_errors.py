import pandas as pd
import os
import time
import json
import re
from groq import RateLimitError
from src.utils import load_settings, load_criteria
from src.pdf_utils import extract_text_from_pdf
from src.ai_engine import AIEngine

def find_file_recursive(root_dir, target_filename):
    """Recursively searches for a file in a directory tree."""
    for dirpath, _, filenames in os.walk(root_dir):
        if target_filename in filenames:
            return os.path.join(dirpath, target_filename)
    return None

def extract_json_from_text(text):
    """Surgical tool to find JSON inside a messy AI response."""
    try:
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
    except Exception:
        pass
    return None

def robust_analyze(ai, filename, text, inc_list, exc_list, model):
    """
    A manual analysis function that includes KEY ROTATION and SURGICAL EXTRACTION.
    """
    prompt = f"""
    You are a data extraction bot.
    TASK: Analyze this research paper text and return a JSON object.
    
    TEXT:
    {text[:2500]} 
    
    CRITERIA (1=Yes, 0=No):
    Inclusion: {inc_list}
    Exclusion: {exc_list}

    RETURN ONLY VALID JSON.
    Format:
    {{
        "Extracted_Title": "Title",
        "Inclusion_Breakdown": {{ "Inc_1": 0 }},
        "Exclusion_Breakdown": {{ "Exc_1": 0 }},
        "Review_Research_Type": "Research Paper",
        "Insights": "Summary"
    }}
    """

    # --- KEY ROTATION LOOP ---
    max_retries = len(ai.keys) + 2
    
    for attempt in range(max_retries):
        try:
            completion = ai.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a JSON extractor."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            # If successful, extract JSON
            raw_content = completion.choices[0].message.content
            clean_json = extract_json_from_text(raw_content)
            
            if clean_json:
                return clean_json
            else:
                print(f"   ⚠️  Attempt {attempt+1}: AI replied, but JSON parsing failed.")
        
        except RateLimitError:
            print(f"   ⚠️  Rate Limit hit on Key #{ai.current_key_index + 1}. Rotating...")
            ai.switch_key()
            time.sleep(1)
            continue
            
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
            time.sleep(1)

    return None

def main():
    print("--- Retry Failed Papers Script (Rotation + Surgical Mode) ---")
    
    input_excel = "data/results/slr_screened.xlsx"
    if not os.path.exists(input_excel):
        print(f"❌ Excel file not found at: {input_excel}")
        return

    df = pd.read_excel(input_excel)
    
    # Standardize columns
    df['Included/Excluded'] = df['Included/Excluded'].astype(str)
    df['Insights'] = df['Insights'].astype(str)

    error_rows = df[
        (df['Included/Excluded'].str.contains('Error', case=False)) | 
        (df['Insights'].str.contains("API FAILURE", case=False))
    ]
    
    if error_rows.empty:
        print("✅ No errors found! Your file is clean.")
        return

    print(f"Found {len(error_rows)} failed papers. Retrying with full key rotation...")
    
    settings = load_settings()
    inc_list, exc_list = load_criteria()
    ai = AIEngine()
    
    for index, row in error_rows.iterrows():
        filename = row['File Name']
        print(f"\n🔄 Fixing: {filename}")
        
        pdf_path = find_file_recursive(settings["input_folder"], filename)
        if not pdf_path:
            print("   ❌ File lost.")
            continue

        text = extract_text_from_pdf(pdf_path, 3000)
        
        # Call the new robust function
        data = robust_analyze(ai, filename, text, inc_list, exc_list, settings["model_id"])

        if data:
            print("   ✅ Success! Recovered Data.")
            df.at[index, "Research Paper Title"] = data.get("Extracted_Title", filename)
            df.at[index, "Insights"] = data.get("Insights", "Recovered")
            df.at[index, "Review/Research Paper"] = data.get("Review_Research_Type", "Research Paper")
            
            inc_data = data.get("Inclusion_Breakdown", {})
            exc_data = data.get("Exclusion_Breakdown", {})
            
            # Update criteria columns
            for i, crit in enumerate(inc_list):
                if crit in df.columns:
                    df.at[index, crit] = inc_data.get(f"Inc_{i+1}", 0)
            for i, crit in enumerate(exc_list):
                if crit in df.columns:
                    df.at[index, crit] = exc_data.get(f"Exc_{i+1}", 0)

            # Strict Logic Decision
            exc_score = sum(1 for v in exc_data.values() if v == 1)
            inc_score = sum(1 for v in inc_data.values() if v == 1)
            
            if exc_score > 0:
                df.at[index, "Included/Excluded"] = 0
            elif inc_score == 0:
                df.at[index, "Included/Excluded"] = 0
            else:
                df.at[index, "Included/Excluded"] = 1
        else:
            print("   ❌ Failed after trying all keys.")

        # Save constantly
        df.to_excel("slr_screened_complete.xlsx", index=False)

    print(f"\n✨ DONE. Final dataset saved to: slr_screened_complete.xlsx")

if __name__ == "__main__":
    main()