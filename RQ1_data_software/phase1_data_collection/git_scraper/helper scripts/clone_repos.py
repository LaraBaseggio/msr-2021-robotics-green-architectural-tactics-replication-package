import git
import csv
import os
from collections import defaultdict

####################################
#### REMOVE BLANK LINES FROM CSV ###
####################################
def no_blank(fd):
    try:
        while True:
            line = next(fd)
            if len(line.strip()) != 0:
                yield line
    except:
        return

columns = defaultdict(list)
with open('Repos_all.csv') as f:
	reader = csv.DictReader(no_blank(f))
	for row in reader:
		for (k,v) in row.items(): 
			columns[k].append(v)

while '' in columns['URL']:
    columns['URL'].remove('')
print(columns['URL'])

os.makedirs('git_repos', exist_ok=True)

for url in columns['URL']:
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