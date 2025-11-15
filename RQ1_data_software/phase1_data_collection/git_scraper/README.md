# Git Scraper - Execution Guide

This guide provides step-by-step instructions for running all data collection scripts in the git_scraper directory.

## Prerequisites

Ensure you have the following Python packages installed:
- `gitpython` (for cloning and commit extraction)
- `pydriller` (for commit extraction)
- `scrapy` (for web crawlers)

Install with:
```bash
pip install gitpython pydriller scrapy
```

## Step 1: Clone Repositories 

The `helper scripts/clone_repos.py` script clones all repositories from `Repos_all.csv` into the `git_repos/` directory.

**Verify completion:**
```bash
ls git_repos/ | wc -l  # This extarcted 328 repositories
```

---

## Step 2: Extract Local Repository Data

These scripts analyze the cloned repositories in `git_repos/`. They can be run in parallel or sequentially.

### 2.1 Run Both Extractors in Parallel (Recommended)

**Easiest method:** Use the provided script to run both extractors in separate tmux sessions.

**Run:**
```bash
cd /home/lara/msr-2021-robotics-green-architectural-tactics-replication-package/RQ1_data_software/phase1_data_collection/git_scraper
./run_extractors_parallel.sh
```

This will:
- Create two tmux sessions: `git_data_extractor` and `commit_extractor`
- Run both scripts in parallel
- Allow you to monitor each session independently

**To view progress:**
```bash
tmux attach -t git_data_extractor    # View git_data_extractor progress
tmux attach -t commit_extractor        # View commit_extractor progress
```

**To detach from a session:** Press `Ctrl+B`, then `D`

**To list all sessions:**
```bash
tmux ls
```

**To kill sessions when done:**
```bash
tmux kill-session -t git_data_extractor
tmux kill-session -t commit_extractor
```

---

### 2.2 Extract Source Code Comments and Markdown Files

**Script:** `git_data_extractor.py`

**What it does:**
- Extracts C++ comments (`//` and `/* */`) from `.cpp` files
- Extracts Python comments (`#`) from `.py` files
- Extracts contents from `.md` (markdown) files
- Outputs JSON data for each repository

**Run manually:**
```bash
cd /home/lara/msr-2021-robotics-green-architectural-tactics-replication-package/RQ1_data_software/phase1_data_collection/git_scraper
python3 git_data_extractor.py
```

**Output:** `data2/git_repos1_data.json`

**Note:** The script expects repositories to be in `git_repos/` directory.

---

### 2.3 Extract Commit Messages

**Script:** `commit_extractor.py`

**What it does:**
- Extracts commit messages, hashes, and dates from each repository
- Uses pydriller to analyze git history
- Outputs JSON data with commit information

**Run manually:**
```bash
python3 commit_extractor.py
```

**Output:** `data2/commit_data.json`

**Note:** 
- The script reads from `Repos_all.csv` to get repository IDs
- It expects repositories to be in `git_repos/` directory
- The script changes directories during execution (this is expected behavior)

---

## Step 3: Run Web Crawlers (Scrapy Spiders)

These scripts used to scrape GitHub directly for issues and pull requests (web scraping). This caused 429 errors and long waiting times. 
This means they are not actual scrapers anymore - I'm keeping the framework as it is for now, in case the scraper approach wants to be maintained - Later needs to be cleaned up. 

They have all been changes to use the GitHub API key instead (5000 requests/hour). 

**Files:**
- `GitHubWebCrawler/GitHubWebCrawler/spiders/scraper.py` 
- `GitOpenPRWebCrawler/GitOpenPRWebCrawler/spiders/scraper.py` 
- `GitClosedPRWebCrawler/GitClosedPRWebCrawler/spiders/scraper.py` 
- `GitClosedIssuesWebCrawler/GitClosedIssuesWebCrawler/spiders/scrapy.py` 

### 3.2 Run GitHub Open Issues Crawler

**What it does:**
- Crawls GitHub for open issues from repositories in `Repos_all.csv`
- Extracts issue titles, contents, code snippets, quotes, and details

**Output:** `data2/github-open-issues_data.json`

---

### 3.3 Run GitHub Open Pull Requests Crawler

**What it does:**
- Crawls GitHub for open pull requests
- Extracts PR titles, authors, contents, comments, code snippets

**Output:** `data2/github-open-pr_data.json`

---

### 3.4 Run GitHub Closed Pull Requests Crawler

**What it does:**
- Crawls GitHub for closed pull requests
- Same data as open PRs, but with status "Closed"

**Output:** `data2/github-closed-pr_data.json`

---

### 3.5 Run GitHub Closed Issues Crawler

**What it does:**
- Crawls GitHub for closed issues
- Same data as open issues, but with status "Closed"

**Output:** `data2/github-closed-issues_data.json`

**Note:** These crawlers may take a long time and may hit GitHub rate limits. Consider adding delays if needed.

---

## Step 4: Extract BitBucket Pull Requests

**Script:** `bitbucket_pr_extractor.py`

**What it does:**
- Uses BitBucket API to extract declined pull requests
- Extracts PR titles, authors, descriptions, comments, and dates
- Currently configured for 8 specific BitBucket repositories (hardcoded list)

**Run:**
```bash
python3 bitbucket_pr_extractor.py
```

**Output:** `data2/bitbucket_pr_data.json`

**Note:** This script uses the BitBucket API and doesn't require cloned repositories.

---

## Step 5: Analysis (Optional)

**Script:** `count.py`

**What it does:**
- Analyzes and counts data from JSON files
- Compares URLs from CSV with scraped data

**Run:**
```bash
python3 count.py
```

---

## Summary of Output Files

After running all scripts, you should have the following output files:

### Local Repository Data:
- `data2/git_repos1_data.json` - Source code comments and markdown files
- `data2/commit_data3.json` - Commit messages and metadata

### Web Scraped Data:
- `data2/github-open-issues_data.json` - GitHub open issues
- `data2/github-open-pr_data.json` - GitHub open pull requests
- `data2/github-closed-pr_data.json` - GitHub closed pull requests
- `data2/github-closed-issues_data.json` - GitHub closed issues
- `data2/bitbucket_pr_data.json` - BitBucket declined pull requests

---

## Execution Order Summary

1. **Clone repositories** - `helper scripts/clone_repos.py`
2. **Extract local data** (can run in parallel):
   - `git_data_extractor.py`
   - `commit_extractor.py`
3. **Run web crawlers** (update paths first, then run):
   - `GitHubWebCrawler` (open issues)
   - `GitOpenPRWebCrawler` (open PRs)
   - `GitClosedPRWebCrawler` (closed PRs)
   - `GitClosedIssuesWebCrawler` (closed issues)
4. **Extract BitBucket data** - `bitbucket_pr_extractor.py`
5. **Optional analysis** - `count.py`
