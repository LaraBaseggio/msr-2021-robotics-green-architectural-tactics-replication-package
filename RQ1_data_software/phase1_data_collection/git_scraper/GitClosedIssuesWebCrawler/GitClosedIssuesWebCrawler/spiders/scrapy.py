import requests
import csv
import json
import os
import time
import re
from collections import defaultdict
from urllib.parse import urlparse

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

# Configuration
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
API_BASE = 'https://api.github.com'
HEADERS = {
    'Accept': 'application/vnd.github.v3+json',
    'User-Agent': 'GitClosedIssuesScraper'
}
if GITHUB_TOKEN:
    HEADERS['Authorization'] = f'token {GITHUB_TOKEN}'

# Rate limiting: 5000 requests/hour = ~0.72 seconds between requests
RATE_LIMIT_DELAY = 0.72

# Get base directory (git_scraper)
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
repos_csv_path = os.path.join(base_dir, 'Repos_all.csv')
git_repos_dir = os.path.join(base_dir, 'git_repos')
output_file = os.path.join(base_dir, 'data2', 'github-closed-issues_data.json')


def parse_markdown_for_elements(body):
    """Parse markdown body to extract code, quotes, lists, and paragraphs."""
    if not body:
        return {
            'issue_contents': [],
            'issue_code': [],
            'issue_quotes': [],
            'contents_details': [],
            'contents_details_more': []
        }
    
    issue_contents = []
    issue_code = []
    issue_quotes = []
    contents_details = []
    contents_details_more = []
    
    lines = body.split('\n')
    in_code_block = False
    in_quote = False
    
    for line in lines:
        stripped = line.strip()
        
        # Code blocks (```code``` or `code`)
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            issue_code.append(stripped)
            continue
        if stripped.startswith('`') and stripped.endswith('`') and len(stripped) > 2:
            code = stripped.strip('`')
            if code:
                issue_code.append(code)
        
        # Blockquotes (> text)
        if stripped.startswith('>'):
            quote_text = stripped[1:].strip()
            if quote_text:
                issue_quotes.append(quote_text)
            continue
        
        # Lists (- item or * item or 1. item)
        if re.match(r'^[-*]\s+', stripped) or re.match(r'^\d+\.\s+', stripped):
            list_text = re.sub(r'^[-*]\s+', '', re.sub(r'^\d+\.\s+', '', stripped))
            if list_text:
                # Check if it has paragraph content (longer or has newlines)
                if '\n' in list_text or len(list_text) > 100:
                    contents_details.append(list_text)
                else:
                    # Filter out items with newlines for contents_details_more
                    if "\n" not in list_text:
                        contents_details_more.append(list_text)
            continue
        
        # Regular paragraphs
        if stripped and not stripped.startswith('#') and not stripped.startswith('|'):
            issue_contents.append(stripped)
    
    return {
        'issue_contents': issue_contents,
        'issue_code': issue_code,
        'issue_quotes': issue_quotes,
        'contents_details': contents_details,
        'contents_details_more': contents_details_more
    }


def get_repo_owner_and_name(github_url):
    """Extract owner and repo name from GitHub URL."""
    parsed = urlparse(github_url)
    path_parts = [p for p in parsed.path.split('/') if p]
    if len(path_parts) >= 2:
        owner = path_parts[0]
        repo = path_parts[1].rstrip('.git')
        return owner, repo
    return None, None


def fetch_closed_issues(owner, repo):
    """Fetch all closed issues for a repository."""
    url = f'{API_BASE}/repos/{owner}/{repo}/issues'
    params = {
        'state': 'closed',
        'per_page': 100,
        'page': 1
    }
    
    all_issues = []
    
    while True:
        try:
            response = requests.get(url, headers=HEADERS, params=params)
            
            if response.status_code == 200:
                issues = response.json()
                if not issues:
                    break
                
                # Filter out pull requests (issues API returns both issues and PRs)
                # PRs have 'pull_request' field, issues don't
                issues_only = [issue for issue in issues if 'pull_request' not in issue]
                all_issues.extend(issues_only)
                
                # Check if there are more pages
                if 'next' in response.links:
                    params['page'] += 1
                else:
                    break
                    
            elif response.status_code == 429:
                reset_time = int(response.headers.get('X-RateLimit-Reset', time.time() + 60))
                wait_time = max(reset_time - int(time.time()), 0) + 10
                print(f"  Rate limited! Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
                
            elif response.status_code == 404:
                print(f"  Repository {owner}/{repo} not found or inaccessible")
                break
                
            else:
                print(f"  Error {response.status_code}: {response.text[:100]}")
                break
            
            time.sleep(RATE_LIMIT_DELAY)
            
        except Exception as e:
            print(f"  Error fetching issues: {e}")
            break
    
    return all_issues


def process_issue(issue_data):
    """Process a single issue and extract all required fields."""
    body = issue_data.get('body', '')
    parsed = parse_markdown_for_elements(body)
    
    # Build item matching the Scrapy output format
    item = {
        'url': issue_data.get('html_url', ''),
        'issue_title': issue_data.get('title', '').strip() if issue_data.get('title') else '',
        'issue_status': 'Closed',
        'posted_on': issue_data.get('created_at', '') if issue_data.get('created_at') else '',
        'issue_contents': parsed['issue_contents'] if parsed['issue_contents'] else [],
        'issue_code': parsed['issue_code'] if parsed['issue_code'] else [],
        'issue_quotes': parsed['issue_quotes'] if parsed['issue_quotes'] else [],
        'contents_details': parsed['contents_details'] if parsed['contents_details'] else [],
        'contents_details_more': parsed['contents_details_more'] if parsed['contents_details_more'] else []
    }
    
    return item


# Main execution
if __name__ == '__main__':
    print("=" * 70)
    print("GitHub API Closed Issues Scraper")
    print("=" * 70)
    
    if not GITHUB_TOKEN:
        print("WARNING: No GITHUB_TOKEN found in environment!")
        print("Set it with: export GITHUB_TOKEN=your_token")
        print("Without token: 60 requests/hour limit")
        print("With token: 5,000 requests/hour limit")
        print()
    
    # Read CSV
    columns = defaultdict(list)
    with open(repos_csv_path) as f:
        reader = csv.DictReader(no_blank(f))
        for row in reader:
            for (k, v) in row.items():
                columns[k].append(v)
    
    while '' in columns['URL']:
        columns['URL'].remove('')
    
    # Filter GitHub URLs
    git_urls = [s for s in columns['URL'] if "github.com" in s]
    
    # Check if repositories exist in git_repos/
    existing_repo_urls = []
    for url in git_urls:
        repo_name = url.rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        
        repo_path = os.path.join(git_repos_dir, repo_name)
        if os.path.exists(repo_path) and os.path.isdir(repo_path):
            if os.path.exists(os.path.join(repo_path, '.git')):
                existing_repo_urls.append(url)
    
    print(f"Found {len(existing_repo_urls)} existing repositories out of {len(git_urls)} GitHub repositories")
    print()
    
    # Create output directory
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    processed_repos = set()
    if os.path.exists(output_file):
      try:
          with open(output_file, 'r') as f:
              for line in f:
                  line = line.strip()
                  if not line:
                      continue
                  try:
                      data = json.loads(line)
                      url = data.get('url', '')
                      if '/issues/' in url:
                          parts = url.split('/')
                          if len(parts) >= 5:
                              repo_key = f"{parts[3]}/{parts[4]}"
                              processed_repos.add(repo_key)
                  except:
                      continue
          print(f"Found {len(processed_repos)} already processed repositories")
          print()
      except:
          print("Could not load existing file, starting fresh")
          print()

    # Process each repository
    total_repos = len(existing_repo_urls)

    for idx, url in enumerate(existing_repo_urls, 1):
        owner, repo = get_repo_owner_and_name(url)
        if not owner or not repo:
            print(f"[{idx}/{total_repos}] Skipping invalid URL: {url}")
            continue

        repo_key = f"{owner}/{repo}"
        if repo_key in processed_repos:
            print(f"[{idx}/{total_repos}] Skipping {owner}/{repo} (already processed)")
            continue

        print(f"[{idx}/{total_repos}] Processing {owner}/{repo}...")

        # Fetch closed issues
        issues = fetch_closed_issues(owner, repo)
        print(f"  Found {len(issues)} closed issues")

        # Process issues
        repo_items = [process_issue(issue) for issue in issues]

        # Append new items to output file
        print(f"  Saving {len(repo_items)} items to {output_file}...")
        with open(output_file, 'a') as f:
            for item in repo_items:
                f.write(json.dumps(item) + '\n')
        print("  Saved.")

        # Mark repo as processed to avoid processing again later
        processed_repos.add(repo_key)
        print()