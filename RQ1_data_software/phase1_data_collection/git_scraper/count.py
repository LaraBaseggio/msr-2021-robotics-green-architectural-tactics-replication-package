import csv
import json
from collections import defaultdict

def no_blank(fd):
    try:
        while True:
            line = next(fd)
            if len(line.strip()) != 0:
                yield line
    except:
        return

with open('8_github_with_launch_files.json') as f:
	repos_data = json.load(f)

urls = [repo['html_url'] for repo in repos_data if 'html_url' in repo and repo['html_url']]

with open('data2/github-closed-pr-final_data.json') as f:
    d = json.load(f)
    #print(d)
with open('data2/github-open-pr_data.json') as f:
    e = json.load(f)

file_url = [item.get('url') for item in d]
new_url = []
for url in file_url:
	url = url.split('/pull')[0]
	new_url.append(url)

file_url1 = [item.get('url') for item in e]
new_url1 = []
for url in file_url1:
    url = url.split('/pull')[0]
    new_url1.append(url)

print(len(set(new_url)))
print(len(set(new_url1)))
print(len(list(set(new_url+new_url1))))
#git_issues = list(set(new_url)) + list(set(new_url1))
#print(len(git_issues))
#output = list(set(columns['URL']) - set(new_url))
#print(len(output))