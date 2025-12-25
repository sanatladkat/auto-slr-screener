import os
import json
import time
from groq import Groq, RateLimitError
from dotenv import load_dotenv
from src.logger import setup_logger

load_dotenv()
logger = setup_logger()

class AIEngine:
    def __init__(self):
        # Load keys from .env
        keys_str = os.getenv("GROQ_API_KEYS") or os.getenv("GROQ_API_KEY")
        if not keys_str:
            logger.critical("FATAL: No API keys found in .env.")
            raise ValueError("FATAL: No API keys found.")
        
        # Clean and store keys
        self.keys = [k.strip() for k in keys_str.split(',') if k.strip()]
        self.current_key_index = 0
        
        # Initialize first key
        self.client = Groq(api_key=self.keys[0])
        
        # Log startup (Masked key)
        masked = "..." + self.keys[0][-4:]
        logger.info(f"🔹 AI Engine Initialized with {len(self.keys)} keys. Active: Key #1 ({masked})")

    def switch_key(self):
        """Switches to the next available API key."""
        self.current_key_index = (self.current_key_index + 1) % len(self.keys)
        new_key = self.keys[self.current_key_index]
        masked = "..." + new_key[-4:]
        
        logger.warning(f"⚠️ Rate Limit Hit! Rotating to Key #{self.current_key_index + 1} ({masked})...")
        self.client = Groq(api_key=new_key)

    def analyze_paper(self, filename, text, inclusion, exclusion, model, temperature):
        # Format criteria
        inc_str = "\n".join([f"{i+1}. {c}" for i, c in enumerate(inclusion)])
        exc_str = "\n".join([f"{i+1}. {c}" for i, c in enumerate(exclusion)])

        # JSON Template
        inc_keys = {f"Inc_{i+1}": 0 for i in range(len(inclusion))}
        exc_keys = {f"Exc_{i+1}": 0 for i in range(len(exclusion))}
        
        example_json = {
            "Extracted_Title": "Full Title",
            "Inclusion_Breakdown": inc_keys,
            "Exclusion_Breakdown": exc_keys,
            "Review_Research_Type": "Research Paper",
            "Publication_Type": "Journal",
            "Publisher": "IEEE",
            "Venue_Name": "IEEE Access",
            "First_Author_Name": "Name",
            "First_Author_Country": "Country",
            "Study_Area_Country": "Country",
            "Insights": "Summary"
        }
        
        prompt = f"""
        You are a strict Research Assistant for a Systematic Literature Review.
        FILE: {filename}
        TEXT: {text}

        TASK: 
        1. Extract Metadata.
        2. Evaluate EACH criteria strictly.
        
        CRITICAL CONTEXT:
        - Synonyms for Sugarcane: "Saccharum", "Saccharum officinarum", "Sugar crop".
        - Diseases: "Pokkah Boeng", "Red Rot", "Smut", "Grassy Shoot", "White Leaf", "Yellow Leaf".
        - AI Methods: "Deep Learning", "CNN", "SVM", "Random Forest", "Fuzzy Logic", "UAV imagery".

        INCLUSION CRITERIA (1 = Met, 0 = Not Met):
        {inc_str}

        EXCLUSION CRITERIA (1 = Met [Exclude], 0 = Not Met [Keep]):
        {exc_str}

        OUTPUT FORMAT (JSON ONLY):
        {json.dumps(example_json)}
        """

        max_retries = len(self.keys) + 2
        last_error = "Unknown Error" # Initialize variable to prevent UnboundLocalError
        
        for attempt in range(max_retries):
            try:
                # Log usage
                if attempt == 0:
                    logger.debug(f"Processing: {filename} (Key #{self.current_key_index + 1})")

                completion = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a JSON-only bot. Extract metadata and flag criteria."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    response_format={"type": "json_object"}
                )
                
                logger.info(f"✅ AI Success: {filename}")
                return json.loads(completion.choices[0].message.content)
            
            except RateLimitError:
                if attempt < max_retries - 1:
                    logger.warning(f"Rate Limit (429) on {filename}. Switching keys...")
                    self.switch_key()
                    continue
                else:
                    last_error = "Rate Limit Exhausted"
                    logger.error(f"❌ All {len(self.keys)} keys exhausted on {filename}.")

            except Exception as e:
                # Capture the error message here so it survives the loop
                last_error = str(e)
                logger.error(f"⚠️ API Error (Attempt {attempt+1}) on {filename}: {last_error}")
                time.sleep(2)

        # Permanent Failure
        logger.error(f"🚨 PERMANENT FAILURE: {filename}")
        return {
            "Research Paper Title": "Error",
            "Inclusion_Breakdown": inc_keys,
            "Exclusion_Breakdown": exc_keys,
            "Included/Excluded": 0,
            "Insights": f"API FAILURE: {last_error}", # Now safely uses last_error
            "Category": "Error",
            "Publication": "Error",
            "Journal/Conference Paper": "Error",
            "First Author Name": "Error",
            "First Author’s Country Name": "Error",
            "Study Area Country Name": "Error"
        }