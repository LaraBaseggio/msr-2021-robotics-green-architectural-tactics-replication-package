import pymongo
from pymongo import MongoClient
import json
import os
from pathlib import Path

username = os.getenv("MONGO_USER")
password = os.getenv("MONGO_PASSWORD")
MONGO_URI = (
    f"mongodb+srv://{username}:{password}"
    "@ros-data.ujsrakb.mongodb.net/data_phase1"
    "?ssl=true&ssl_cert_reqs=CERT_NONE"
)
# File to collection mapping
FILE_COLLECTION_MAP = {
    'github-closed-pr_data.json': 'GitHubClosedPRs',
    'github-open-pr_data.json': 'GitHubOpenPRs',
    'github-closed-issues_data.json': 'GitHubClosedIssues',
    'github-open-issues_data.json': 'GitHubOpenIssues',
    'bitbucket_pr_data.json': 'BitbucketPRs',
    'commit_data.json': 'Commits',
    'git_repos1_data.json': 'GitRepos',
}

# Base directory (phase1_data_collection)
BASE_DIR = Path(__file__).parent
GIT_SCRAPER_DATA2_DIR = BASE_DIR / 'git_scraper' / 'data2'

def load_json_file(file_path):
    """Load JSON file, handling both array format and newline-delimited format."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return []
            
            # Try parsing as JSON array first
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    return data
                else:
                    return [data]
            except json.JSONDecodeError:
                # Try parsing as newline-delimited JSON
                items = []
                for line in content.split('\n'):
                    line = line.strip()
                    if line:
                        # Remove trailing comma if present (common in newline-delimited JSON)
                        if line.endswith(','):
                            line = line[:-1].strip()
                        try:
                            items.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
                return items
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return []

def import_to_mongodb(collection, documents, clear_existing=False):
    """Import documents into MongoDB collection."""
    if not documents:
        print(f"  No documents to import")
        return 0
    
    if clear_existing:
        result = collection.delete_many({})
        print(f"  Cleared {result.deleted_count} existing documents")
    
    # Insert documents in batches
    batch_size = 1000
    total_inserted = 0
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        try:
            result = collection.insert_many(batch, ordered=False)
            total_inserted += len(result.inserted_ids)
            print(f"  Inserted batch: {len(batch)} documents (Total: {total_inserted}/{len(documents)})")
        except Exception as e:
            print(f"  Error inserting batch: {e}")
            # Try inserting one by one to find problematic documents
            for doc in batch:
                try:
                    collection.insert_one(doc)
                    total_inserted += 1
                except Exception as e2:
                    print(f"    Skipped document due to error: {e2}")
    
    return total_inserted

def main():
    # Connect to MongoDB
    print("Connecting to MongoDB...")
    try:
        client = MongoClient(MONGO_URI)
        db = client.data_phase1
        # Test connection
        client.admin.command('ping')
        print("Connected successfully\n")
    except Exception as e:
        print(f"Connection failed: {e}")
        return
    
    # Process files from git_scraper/data2 directory
    print("Processing files from git_scraper/data2/...")
    data2_path = GIT_SCRAPER_DATA2_DIR.resolve()
    
    for filename, collection_name in FILE_COLLECTION_MAP.items():
        file_path = data2_path / filename
        
        if not file_path.exists():
            print(f"\nSkipping {filename} - file not found")
            continue
        
        print(f"\nProcessing {filename} → {collection_name}")
        print(f"   File: {file_path}")
        
        # Load JSON data
        documents = load_json_file(file_path)
        print(f"   Loaded {len(documents)} documents")
        
        if documents:
            # Get collection
            collection = db[collection_name]
            
            # Ask user if they want to clear existing data
            existing_count = collection.count_documents({})
            if existing_count > 0:
                response = input(f"   Collection has {existing_count} existing documents. Clear and replace? (y/n): ")
                clear_existing = response.lower() == 'y'
            else:
                clear_existing = False
            
            # Import to MongoDB
            inserted = import_to_mongodb(collection, documents, clear_existing)
            print(f"   Successfully imported {inserted} documents")
        else:
            print(f"   No documents found in file")
    
    print("\n" + "="*70)
    print("Import complete!")
    print("="*70)
    
    # Show summary
    print("\nCollection Summary:")
    for collection_name in FILE_COLLECTION_MAP.values():
        count = db[collection_name].count_documents({})
        print(f"  {collection_name}: {count} documents")

if __name__ == "__main__":
    main()