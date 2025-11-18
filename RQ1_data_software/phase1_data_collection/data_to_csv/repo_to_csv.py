import csv
import json
from itertools import zip_longest
from collections import defaultdict
import re
from collections import Counter
def no_blank(fd):
    try:
        while True:
            line = next(fd)
            if len(line.strip()) != 0:
                yield line
    except:
        return

def return_longest_list(list1, list2, list3):
    if (len(list1) > len(list2) and len(list1) > len(list3)):
        return list1
    elif (len(list2) > len(list1) and len(list2) > len(list3)):
        return list2
    elif (len(list3) > len(list1) and len(list3) > len(list2)):
        return list3
    # else:
    #     return list1
    else:
        if (len(list1) != 0):
            return list1
        elif (len(list2) != 0):
            return list2
        elif (len(list3) != 0):
            return list3

columns = defaultdict(list)
with open('Repos_all.csv') as f:
    reader = csv.DictReader(no_blank(f))
    for row in reader:
        for (k,v) in row.items(): 
            columns[k].append(v)

while '' in columns['URL']:
    columns['URL'].remove('')

with open('../git_scraper/data2/git_repos1_data.json') as f:
    # Handle JSONL format (one JSON object per line) or multiple JSON objects
    repo_data = []
    content = f.read()
    
    # First, try to parse as a single JSON array/object
    try:
        repo_data = json.loads(content)
        if not isinstance(repo_data, list):
            repo_data = [repo_data]
    except json.JSONDecodeError:
        # If that fails, try JSONL format (one JSON object per line)
        repo_data = []
        for line in content.split('\n'):
            line = line.strip()
            if line:
                try:
                    repo_data.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        
        # If JSONL didn't work, try to extract concatenated JSON objects
        if not repo_data:
            decoder = json.JSONDecoder()
            idx = 0
            content_remaining = content
            while idx < len(content_remaining):
                # Skip whitespace and commas (JSON objects may be separated by commas)
                while idx < len(content_remaining) and (content_remaining[idx].isspace() or content_remaining[idx] == ','):
                    idx += 1
                if idx >= len(content_remaining):
                    break
                try:
                    obj, end_idx = decoder.raw_decode(content_remaining[idx:])
                    repo_data.append(obj)
                    idx += end_idx
                except (json.JSONDecodeError, ValueError):
                    break

repo_url = []
repo_name = [item.get('git_repo_name') for item in repo_data]
repo_name_new = []
repo_indices = []  # Track which original repo index each matched entry corresponds to
repo_md_contents = [item.get('md_contents') for item in repo_data]
repo_md_file = [item.get('md_file_names') for item in repo_data]
repo_code_c = [item.get('code_comments_c++') for item in repo_data]
repo_code_p = [item.get('code_comments_python') for item in repo_data]
repo_id = []
collection_name = []
new_dicts_md = []
new_dicts_p = []
new_dicts_c = []
new_repo_url = []
new_repo_url1 = []
new_repo_name = []
new_repo_name1 = []

for i, name in enumerate(repo_name):
    for url in columns['URL']:
        if url.endswith(name):
            print(name+": ",url)
            repo_url.append(url)
            repo_name_new.append(name)
            repo_indices.append(i)  # Track the original repository index
print(len(repo_url))
print(len(repo_name_new))
print(len(repo_name))

repo_name = repo_name_new
#print(len(repo_name))
# print(len(set(repo_name)))
d =  Counter(repo_name)
res = [k for k, v in d.items() if v > 1]
#print(res)

def flatten_and_join(value):
    """Flatten nested lists and join into a single string."""
    if isinstance(value, list):
        # Flatten nested lists
        flattened = []
        for item in value:
            if isinstance(item, list):
                flattened.extend(item)
            else:
                flattened.append(item)
        return ''.join(str(x) for x in flattened)
    return str(value) if value else ''

for mcontents in repo_md_contents:
    for key in mcontents.keys():
        mcontents[key] = flatten_and_join(mcontents[key])

for cpp in repo_code_c:
    for key in cpp.keys():
        cpp[key] = flatten_and_join(cpp[key])

for py in repo_code_p:
    for key in py.keys():
        py[key] = flatten_and_join(py[key])

# # print(len(repo_md_contents))
# # print(len(repo_code_c))
# # print(len(repo_code_p))

for c in repo_code_c:
    if (len(c.keys()) == 0):
        c['message'] = 'no data'
    for k, v in c.items():
        new_code_c = {}
        new_code_c[k] = v
        new_dicts_c.append(new_code_c)

#print(new_dicts_c)

for p in repo_code_p:
    if (len(p.keys()) == 0):
        p['message'] = 'no data'
    for k, v in p.items():
        new_code_p = {}
        new_code_p[k] = v
        new_dicts_p.append(new_code_p)
#print(len(new_dicts_p))

for m in repo_md_contents:
    if (len(m.keys()) == 0):
        m['message'] = 'no data'
    for k, v in m.items():
        new_md = {}
        new_md[k] = v
        new_dicts_md.append(new_md)
#print(new_dicts_md)


for i, url in enumerate(repo_url):
    repo_idx = repo_indices[i]  # Get the original repository index
    longest_list = return_longest_list(repo_code_p[repo_idx], repo_md_contents[repo_idx], repo_code_c[repo_idx])
    new_repo_url.append([url] * len(repo_code_p[repo_idx]))

for url_list in new_repo_url:
    for url in url_list:
        new_repo_url1.append(url)

for i, name in enumerate(repo_name):
    repo_idx = repo_indices[i]  # Get the original repository index
    longest_list = return_longest_list(repo_code_p[repo_idx], repo_md_contents[repo_idx], repo_code_c[repo_idx])
    new_repo_name.append([name] * len(repo_code_p[repo_idx]))

for name_list in new_repo_name:
    for name in name_list:
        new_repo_name1.append(name)

for i in range(len(new_repo_name1)):
    y = "REPO_P" + str(i)
    repo_id.append(y)

for i in range(len(new_repo_name1)):
    collection_name.append("Repositories")

print(len(repo_id))
print(len(new_repo_url1))
print(len(new_repo_name1))
print(len(collection_name))
print(len(new_dicts_md))
print(len(new_dicts_p))
print(len(new_dicts_c))





repo_list = [repo_id,
             new_repo_url1,
             new_repo_name1,
             collection_name,
             new_dicts_p
             ]

export_data = zip_longest(*repo_list, fillvalue='')

with open('data/repo_split_p.csv', 'w', newline='') as myfile:
    wr = csv.writer(myfile)
    wr.writerow(("ID", "URL", "Repo Name", "Collection", "Contents"))
    # wr.writerow(("ID", "URL", "Repo Name", "Collection", "MD Contents"))
    wr.writerows(export_data)
myfile.close()
