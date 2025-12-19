import git
import json
import os
from pydriller import Repository

def switch_to_dir(dir_name):
    print("Current Working Directory " , os.getcwd())
    try: 
        os.chdir(dir_name)
        print("Directory changed")
    except OSError:
        print("Can't change the Current Working Directory") 
    print("Current Working Directory " , os.getcwd())  

# Path to the JSON file
json_file = '8_github_with_launch_files.json'

if not os.path.exists(json_file):
    print(f"Error: Could not find {json_file}")
    exit(1)

with open(json_file, 'r') as f:
    repos_data = json.load(f)

repo_names = []
repo_urls = []

# Extract names and URLs from JSON
for repo in repos_data:
    if 'name' in repo and 'html_url' in repo:
        repo_names.append(repo['name'])
        repo_urls.append(repo['html_url'])

print(f"Loaded {len(repo_names)} repositories from JSON.")

# Base directory (git_scraper)
base_dir = os.getcwd()

for name in repo_names:
    git_repos_path = os.path.join(base_dir, 'git_repos')
    repo_path = os.path.join(git_repos_path, name)
    
    # Check if repository directory exists
    if not os.path.exists(repo_path) or not os.path.isdir(repo_path):
        print(f"Skipping {name} - repository not found in git_repos/")
        continue
    
    # Check if it's a valid git repository
    if not os.path.exists(os.path.join(repo_path, '.git')):
        print(f"Skipping {name} - not a valid git repository")
        continue
    
    commit_msg_data = []
    commit_data = {}

    try:
        # Move into git_repos to maintain compatibility with existing logic if needed
        # though pydriller can take absolute paths
        switch_to_dir(git_repos_path)
        
        print(f"Processing {name}...")
        
        # Use pydriller to traverse commits
        # Passing 'name' since we are inside 'git_repos'
        for commit in Repository(name).traverse_commits():
            commit_dict = {
                'hash': commit.hash,
                'msg': commit.msg,
                'date': str(commit.committer_date)
            }
            commit_msg_data.append(commit_dict)

        print(f"Extracted {len(commit_msg_data)} commit(s) from {name}")
        
        commit_data['repo_name'] = name
        # Find the URL for this repo name
        commit_data['url'] = next((url for n, url in zip(repo_names, repo_urls) if n == name), "")
        commit_data['commit_info'] = commit_msg_data
        
        # Return to base directory to save output
        switch_to_dir(base_dir)
        
        os.makedirs('data2', exist_ok=True)
        with open('data2/commit_data.json', 'a') as outfile:
            outfile.write(json.dumps(commit_data))
            outfile.write(",")
            outfile.write("\n")
            
    except Exception as e:
        print(f"Error processing {name}: {str(e)}")
        switch_to_dir(base_dir)
        continue








