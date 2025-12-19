import git
import json
import os

# Path to the JSON file containing repository information
json_file = '8_github_with_launch_files.json'

if not os.path.exists(json_file):
    # Try parent directory if not found (in case script is run from 'helper scripts')
    json_file = os.path.join('..', '8_github_with_launch_files.json')

if not os.path.exists(json_file):
    print(f"Error: Could not find {json_file}")
    exit(1)

with open(json_file, 'r') as f:
    repos = json.load(f)

urls = [repo['html_url'] for repo in repos if 'html_url' in repo and repo['html_url']]

print(f"Found {len(urls)} repositories to clone.")

os.makedirs('git_repos', exist_ok=True)

for url in urls:
	# Extract repo name from URL
	# Handle URLs like: https://github.com/owner/repo or https://github.com/owner/repo.git
	repo_name = url.rstrip('/').split('/')[-1]
	if repo_name.endswith('.git'):
		repo_name = repo_name[:-4]
	
	repo_path = os.path.join('git_repos', repo_name)
	
	# Check if repo has already been cloned
	if os.path.exists(repo_path) and os.path.isdir(repo_path):
		# Verify it's actually a git repository
		if os.path.exists(os.path.join(repo_path, '.git')):
			print(f"Skipping {repo_name} - already cloned")
			continue
	
	# Try to clone the repository
	try:
		print(f"Cloning {url}...")
		git.Git("git_repos").clone(url)
		print(f"Successfully cloned {repo_name}")
	except git.exc.GitCommandError as e:
		print(f"Error cloning {url}: Repository not found or inaccessible")
		continue
	except Exception as e:
		print(f"Error cloning {url}: {str(e)}")
		continue