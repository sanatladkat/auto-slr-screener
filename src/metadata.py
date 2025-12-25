import os
import re

def extract_metadata(filepath):
    # Normalize path separators
    filepath = os.path.normpath(filepath)
    path_parts = filepath.split(os.sep)
    filename = path_parts[-1]
    
    metadata = {
        "File Name": filename,           # Keep track of the file
        "Category": "Unknown",
        "Database": "Unknown",
        "Year": "Unknown",
        "Research Paper Title": "Pending AI Extraction", # Placeholder
        "Filepath": filepath
    }

    # Extract Database (Parent) and Category (Grandparent)
    if len(path_parts) > 1:
        metadata["Database"] = path_parts[-2]
    if len(path_parts) > 2:
        metadata["Category"] = path_parts[-3]

    # Extract Year (Matches "2021-..." or "2021 ...")
    year_match = re.search(r'^(\d{4})', filename)
    if year_match:
        metadata["Year"] = year_match.group(1)

    return metadata