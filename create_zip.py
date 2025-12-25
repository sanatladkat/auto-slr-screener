import os
import zipfile

def zip_project():
    output_filename = "SLR_Project_Submission.zip"
    print(f"📦 Packaging project into '{output_filename}'...")

    # Files/Folders to INCLUDE
    include_files = [
        "main.py",
        "retry_errors.py",
        "requirements.txt",
        "README.md",
        "slr_screened_complete.xlsx", # The most important result!
    ]
    
    include_dirs = [
        "src",
        "config"
    ]

    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 1. Add specific files
        for file in include_files:
            if os.path.exists(file):
                print(f"   + Adding: {file}")
                zipf.write(file)
            else:
                print(f"   ⚠️ Warning: {file} missing!")

        # 2. Add specific directories (Code only)
        for directory in include_dirs:
            if os.path.exists(directory):
                print(f"   + Adding Folder: {directory}/")
                for root, _, files in os.walk(directory):
                    for file in files:
                        if not file.endswith(".pyc") and "__pycache__" not in root:
                            file_path = os.path.join(root, file)
                            zipf.write(file_path)

    print(f"\n✅ Done! File created: {output_filename}")

if __name__ == "__main__":
    zip_project()