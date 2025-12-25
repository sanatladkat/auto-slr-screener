import os
import yaml

def load_settings(config_path="config/settings.yaml"):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Missing config file: {config_path}")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f) or {}

def load_criteria(config_folder="config"):
    inc_path = os.path.join(config_folder, "inclusion.txt")
    exc_path = os.path.join(config_folder, "exclusion.txt")
    
    inclusion = []
    exclusion = []

    if os.path.exists(inc_path):
        with open(inc_path, 'r', encoding='utf-8') as f:
            inclusion = [line.strip() for line in f if line.strip()]
            
    if os.path.exists(exc_path):
        with open(exc_path, 'r', encoding='utf-8') as f:
            exclusion = [line.strip() for line in f if line.strip()]

    return inclusion, exclusion

def ensure_directories(settings):
    output_file = settings.get("output_file", "data/results/slr_screened.xlsx")
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)