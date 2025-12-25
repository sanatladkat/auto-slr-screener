import os
import hashlib

def calculate_md5(file_path):
    """Generates a unique 'fingerprint' (hash) for a file's content."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except OSError:
        return None

def main():
    print("🕵️‍♂️ Scanning for Duplicates in 'data/raw_pdfs'...\n")
    
    root_dir = os.path.join(os.getcwd(), "data", "raw_pdfs")
    
    # Store files as: { 'hash123': ['path/to/file1.pdf', 'path/to/copy.pdf'] }
    content_map = {}
    # Store filename collisions: { 'paper.pdf': ['folder1/paper.pdf', 'folder2/paper.pdf'] }
    name_map = {}
    
    total_files = 0
    
    # 1. Walk through every folder
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if not filename.lower().endswith(".pdf"):
                continue
                
            full_path = os.path.join(dirpath, filename)
            total_files += 1
            
            # Check Name Collision
            if filename not in name_map:
                name_map[filename] = []
            name_map[filename].append(full_path)
            
            # Check Content Collision (The real truth)
            file_hash = calculate_md5(full_path)
            if file_hash:
                if file_hash not in content_map:
                    content_map[file_hash] = []
                content_map[file_hash].append(full_path)

    # 2. Analyze Results
    duplicate_contents = {k: v for k, v in content_map.items() if len(v) > 1}
    duplicate_names = {k: v for k, v in name_map.items() if len(v) > 1}

    print(f"📊 Scan Complete. Analyzed {total_files} files.\n")

    # 3. Report Name Duplicates (likely your issue)
    print(f"🚩 **Duplicate Filenames Found:** {len(duplicate_names)}")
    if duplicate_names:
        print("   (These are files with the EXACT same name in different folders)")
        count = 0
        for name, paths in duplicate_names.items():
            print(f"   📂 '{name}' appears {len(paths)} times:")
            for p in paths:
                # Show just the last part of the path for readability
                short_path = "..." + p[-60:] if len(p) > 60 else p
                print(f"      - {short_path}")
            count += 1
            if count >= 5:
                print(f"      ... and {len(duplicate_names) - 5} more.")
                break
    
    print("-" * 50)

    # 4. Report Content Duplicates
    print(f"🚩 **Exact Content Copies Found:** {len(duplicate_contents)}")
    if duplicate_contents:
        print("   (These files have identical content, even if names differ)")
        count = 0
        for file_hash, paths in duplicate_contents.items():
            print(f"   💾 Group (Hash: {file_hash[:8]}...) has {len(paths)} copies:")
            for p in paths:
                short_path = "..." + p[-60:] if len(p) > 60 else p
                print(f"      - {short_path}")
            count += 1
            if count >= 5:
                print(f"      ... and {len(duplicate_contents) - 5} more.")
                break

    # 5. Summary
    unique_count = len(content_map)
    print("\n" + "="*50)
    print(f"✅ True Unique Files: {unique_count}")
    print(f"❌ Redundant Copies:  {total_files - unique_count}")
    print("="*50)

if __name__ == "__main__":
    main()