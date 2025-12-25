from pypdf import PdfReader
import logging

logging.basicConfig(filename='pdf_errors.log', level=logging.ERROR)

def extract_text_from_pdf(pdf_path, char_limit=3500):
    text = ""
    try:
        reader = PdfReader(pdf_path)
        
        # Handle Encrypted Files
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except:
                logging.error(f"Encrypted PDF skipped: {pdf_path}")
                return ""

        # Extract Page 1
        if len(reader.pages) > 0:
            text += reader.pages[0].extract_text() or ""
            
            # If Page 1 is too short (e.g., Title Page only), grab Page 2
            if len(text) < 500 and len(reader.pages) > 1:
                text += "\n" + (reader.pages[1].extract_text() or "")

    except Exception as e:
        logging.error(f"Corrupt PDF {pdf_path}: {e}")
        return ""

    return text[:char_limit]