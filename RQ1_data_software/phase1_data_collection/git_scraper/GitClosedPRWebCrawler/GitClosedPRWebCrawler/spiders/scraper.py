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
    'User-Agent': 'GitClosedPRScraper'
}
if GITHUB_TOKEN:
    HEADERS['Authorization'] = f'token {GITHUB_TOKEN}'

# Rate limiting: 5000 requests/hour = ~0.72 seconds between requests
RATE_LIMIT_DELAY = 0.72

# Get base directory (git_scraper)
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
json_file_path = os.path.join(base_dir, '8_github_with_launch_files.json')
git_repos_dir = os.path.join(base_dir, 'git_repos')
output_file = os.path.join(base_dir, 'data2', 'github-closed-pr_data.json')


def parse_markdown_for_elements(body):
    """Parse markdown body to extract code, quotes, lists, and paragraphs."""
    if not body:
        return {
            'pr_contents': [],
            'pr_code': [],
            'pr_quotes': [],
            'pr_details': [],
            'pr_details_more': []
        }
    
    pr_contents = []
    pr_code = []
    pr_quotes = []
    pr_details = []
    pr_details_more = []
    
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
            pr_code.append(stripped)
            continue
        if stripped.startswith('`') and stripped.endswith('`') and len(stripped) > 2:
            code = stripped.strip('`')
            if code:
                pr_code.append(code)
        
        # Blockquotes (> text)
        if stripped.startswith('>'):
            quote_text = stripped[1:].strip()
            if quote_text:
                pr_quotes.append(quote_text)
            continue
        
        # Lists (- item or * item or 1. item)
        if re.match(r'^[-*]\s+', stripped) or re.match(r'^\d+\.\s+', stripped):
            list_text = re.sub(r'^[-*]\s+', '', re.sub(r'^\d+\.\s+', '', stripped))
            if list_text:
                if '\n' in list_text or len(list_text) > 100:
                    pr_details.append(list_text)
                else:
                    pr_details_more.append(list_text)
            continue
        
        # Regular paragraphs
        if stripped and not stripped.startswith('#') and not stripped.startswith('|'):
            pr_contents.append(stripped)
    
    return {
        'pr_contents': pr_contents,
        'pr_code': pr_code,
        'pr_quotes': pr_quotes,
        'pr_details': pr_details,
        'pr_details_more': pr_details_more
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


def fetch_pr_comments(owner, repo, pr_number):
    """Fetch comments for a pull request."""
    url = f'{API_BASE}/repos/{owner}/{repo}/issues/{pr_number}/comments'
    comments = []
    
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            comments_data = response.json()
            for comment in comments_data:
                body = comment.get('body', '')
                if body:
                    # Extract paragraph text from comments
                    lines = [line.strip() for line in body.split('\n') if line.strip() and not line.strip().startswith('>')]
                    comments.extend(lines)
        elif response.status_code == 429:
            reset_time = int(response.headers.get('X-RateLimit-Reset', time.time() + 60))
            wait_time = max(reset_time - int(time.time()), 0) + 10
            print(f"  Rate limited on comments, waiting {wait_time} seconds...")
            time.sleep(wait_time)
        time.sleep(RATE_LIMIT_DELAY)
    except Exception as e:
        print(f"  Error fetching comments: {e}")
    
    return comments


def fetch_closed_prs(owner, repo):
    """Fetch all closed pull requests for a repository."""
    url = f'{API_BASE}/repos/{owner}/{repo}/pulls'
    params = {
        'state': 'closed',
        'per_page': 100,
        'page': 1
    }
    
    all_prs = []
    
    while True:
        try:
            response = requests.get(url, headers=HEADERS, params=params)
            
            if response.status_code == 200:
                prs = response.json()
                if not prs:
                    break
                
                all_prs.extend(prs)
                
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
            print(f"  Error fetching PRs: {e}")
            break
    
    return all_prs


def process_pr(pr_data, owner, repo):
    """Process a single PR and extract all required fields."""
    pr_number = pr_data.get('number')
    comments = fetch_pr_comments(owner, repo, pr_number)
    
    body = pr_data.get('body', '')
    parsed = parse_markdown_for_elements(body)
    
    # Build item matching the Scrapy output format
    item = {
        'url': pr_data.get('html_url', ''),
        'pr_title': pr_data.get('title', '').strip(),
        'username': pr_data.get('user', {}).get('login', ''),
        'username_url': pr_data.get('user', {}).get('html_url', ''),
        'issue_status': 'Closed',
        'posted_on': pr_data.get('created_at', ''),
        'pr_contents': parsed['pr_contents'],
        'pr_comments': comments,
        'pr_code': parsed['pr_code'],
        'pr_quotes': parsed['pr_quotes'],
        'pr_details': parsed['pr_details'],
        'pr_details_more': parsed['pr_details_more']
    }
    
    return item


# Main execution
if __name__ == '__main__':
    print("=" * 70)
    print("GitHub API Closed PR Scraper")
    print("=" * 70)
    
    if not GITHUB_TOKEN:
        print("WARNING: No GITHUB_TOKEN found in environment!")
        print("Set it with: export GITHUB_TOKEN=your_token")
        print("Without token: 60 requests/hour limit")
        print("With token: 5,000 requests/hour limit")
        print()
    
    # Read JSON
    if not os.path.exists(json_file_path):
        print(f"Error: Could not find {json_file_path}")
        exit(1)
        
    with open(json_file_path, 'r') as f:
        repos_data = json.load(f)
    
    git_urls = [repo['html_url'] for repo in repos_data if 'html_url' in repo and repo['html_url']]
    
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
    
    # Load existing data if file exists (for resume capability)
    all_items = []
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r') as f:
                all_items = json.load(f)
            print(f"Loaded {len(all_items)} existing items from {output_file}")
            print("(Resuming from previous run)")
            print()
        except:
            print("Could not load existing file, starting fresh")
            print()
    
    # Track processed repos to avoid duplicates
    processed_repos = set()
    if all_items:
        # Extract already processed repos from existing data
        for item in all_items:
            url = item.get('url', '')
            if '/pull/' in url:
                # Extract owner/repo from URL
                parts = url.split('/')
                if len(parts) >= 5:
                    repo_key = f"{parts[3]}/{parts[4]}"
                    processed_repos.add(repo_key)
        print(f"Found {len(processed_repos)} already processed repositories")
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
        
        # Fetch closed PRs
        prs = fetch_closed_prs(owner, repo)
        print(f"  Found {len(prs)} closed PRs")
        
        # Process each PR
        repo_items = []
        for pr in prs:
            item = process_pr(pr, owner, repo)
            repo_items.append(item)
            all_items.append(item)
        
        print(f"  Added {len(repo_items)} PRs from this repo")
        print(f"  Total items collected: {len(all_items)}")
        
        # Save after each repository (incremental save)
        print(f"  Saving progress to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(all_items, f, indent=2)
        print("  Progress saved!")
        print()
    
    print("=" * 70)
    print("Done!")
    print(f"Total items: {len(all_items)}")
    print(f"Output saved to: {output_file}")
    print("=" * 70)
