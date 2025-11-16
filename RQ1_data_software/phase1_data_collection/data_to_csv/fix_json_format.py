#!/usr/bin/env python3
"""
Script to fix JSON format from JSONL (JSON Lines) to proper JSON array format
"""
import json
import os

def fix_jsonl_to_json_array(input_file, output_file):
    """
    Convert JSONL format (one JSON object per line) to proper JSON array format
    """
    data = []
    line_count = 0
    error_count = 0
    
    print(f"Processing {input_file}...")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:  # Skip empty lines
                    try:
                        json_obj = json.loads(line)
                        data.append(json_obj)
                        line_count += 1
                    except json.JSONDecodeError as e:
                        print(f"Error parsing line {line_num}: {e}")
                        print(f"Line content: {line[:100]}...")
                        error_count += 1
                        
        print(f"✅ Successfully parsed {line_count} JSON objects")
        if error_count > 0:
            print(f"⚠️  {error_count} lines had parsing errors")
        
        # Write as proper JSON array
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print(f"✅ Fixed JSON saved to {output_file}")
        print(f"📊 Total records: {len(data)}")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ Input file not found: {input_file}")
        return False
    except Exception as e:
        print(f"❌ Error processing file: {e}")
        return False

def main():
    # File paths
    base_path = "/home/lara/msr-2021-robotics-green-architectural-tactics-replication-package/RQ1_data_software/phase1_data_collection"
    
    files_to_fix = [
        {
            'input': f"{base_path}/git_scraper/data2/github-open-pr_data.json",
            'output': f"{base_path}/git_scraper/data2/github-open-pr_data_fixed.json"
        },
        {
            'input': f"{base_path}/git_scraper/data2/github-closed-pr_data.json",
            'output': f"{base_path}/git_scraper/data2/github-closed-pr_data_fixed.json"
        },
        {
            'input': f"{base_path}/git_scraper/data2/github-closed-issues_data.json",
            'output': f"{base_path}/git_scraper/data2/github-closed-issues_data_fixed.json"
        },
        {
            'input': f"{base_path}/git_scraper/data2/git_repos1_data.json",
            'output': f"{base_path}/git_scraper/data2/git_repos1_data_fixed.json"
        },
        {
            'input': f"{base_path}/data/stackoverflow_new_data.json",
            'output': f"{base_path}/data/stackoverflow_new_data_fixed.json"
        },
        {
            'input': f"{base_path}/data/rosa_new_data.json",
            'output': f"{base_path}/data/rosa_new_data_fixed.json"
        },
        {
            'input': f"{base_path}/data/rosd_new_data.json",
            'output': f"{base_path}/data/rosd_new_data_fixed.json"
        }
    ]
    
    print("🔧 Fixing JSON format for all data files...\n")
    
    for file_info in files_to_fix:
        input_file = file_info['input']
        output_file = file_info['output']
        
        if os.path.exists(input_file):
            print(f"Processing: {os.path.basename(input_file)}")
            success = fix_jsonl_to_json_array(input_file, output_file)
            if success:
                print(f"✅ Fixed: {os.path.basename(output_file)}\n")
            else:
                print(f"❌ Failed: {os.path.basename(input_file)}\n")
        else:
            print(f"⏭️  Skipping (not found): {os.path.basename(input_file)}\n")
    
    print("🎉 JSON format fixing complete!")
    print("\nNext steps:")
    print("1. Update your CSV conversion scripts to use the *_fixed.json files")
    print("2. Run the CSV conversion scripts")

if __name__ == "__main__":
    main()