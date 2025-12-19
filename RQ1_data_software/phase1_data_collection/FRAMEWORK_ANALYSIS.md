# Framework Analysis: Data Collection Framework

## Overview

This framework is a comprehensive data scraping system for collecting robotics software development data from multiple sources. The framework consists of two main components:

1. **Web Crawlers** (`/web_crawlers`) - Scrapes data from web sources using Scrapy
2. **Git Scrapers** (`/git_scraper`) - Extracts data from Git repositories and GitHub/BitBucket APIs

All collected data is saved as JSON files in `/data` (web crawlers) and `/git_scraper/data2` (git scrapers).

---

## Part 1: Web Crawlers Analysis (`/web_crawlers`)

All web crawlers are built using the Scrapy framework and extract data from various ROS-related web sources.

### 1.1 WikiCrawler
**Purpose:** Extracts ROS package documentation from ROS Index and ROS Wiki pages.

**How it works:**
- Starts by fetching package data from ROS Index API (`https://index.ros.org/search/packages/data.humble.json`)
- For each package, extracts: package name, description, and URL
- If a package has a readme, uses it directly
- If no readme exists, visits the package page to find the wiki link
- Follows wiki links to extract detailed package information from ROS Wiki pages
- Parses wiki pages to extract package summaries and details from specific HTML elements

**Data extracted:**
- `package`: Package name
- `package_summary`: Package description/summary
- `package_details`: Detailed package information from wiki pages
- `url`: Package URL

**Output:** JSON data saved to `/data`

---

### 1.2 SOWebCrawler (Stack Overflow Crawler)
**Purpose:** Extracts ROS-related questions and answers from Stack Overflow.

**How it works:**
- Uses Stack Exchange API (not direct web scraping) to avoid 403 errors
- Queries questions tagged with "ros" from Stack Overflow
- Fetches question details including title, body, creation date
- For questions with answers, makes additional API calls to fetch all answers
- Extracts and cleans HTML content, code blocks, and quotes from questions and answers
- Implements pagination to crawl all available questions

**Data extracted:**
- `title`: Question title
- `time`: Creation timestamp
- `post_content`: Cleaned question text (HTML removed)
- `question_code`: Code snippets from question
- `quote`: Blockquotes from question
- `answer`: List of answer texts
- `answer_code`: Code snippets from all answers
- `url`: Question URL

**Output:** JSON data saved to `/data`

---

### 1.3 ROSAWebCrawler (ROS Answers Crawler)
**Purpose:** Extracts questions and answers from ROS Answers (robotics.stackexchange.com).

**How it works:**
- Uses Stack Exchange API for the robotics site
- Fetches questions in batches with pagination
- Implements duplicate detection by checking existing data files
- Groups answers by question ID for efficient processing
- Extracts HTML content, list items, and cleans text
- Uses rate limiting and throttling to respect API limits

**Data extracted:**
- `title`: Question title
- `time`: Creation timestamp
- `post_content`: Cleaned question text
- `question_details`: List items from question body
- `answer`: List of answer texts
- `url`: Question URL

**Output:** JSON data saved to `/data`

---

### 1.4 ROSDWebCrawler (ROS Discourse Crawler)
**Purpose:** Extracts discussion threads from ROS Discourse forum (discourse.openrobotics.org).

**How it works:**
- Crawls 18 predefined category URLs from ROS Discourse
- Uses JSON feed endpoints (`/l/latest.json`) for each category
- Implements pagination (up to 20 pages per category)
- Extracts topic slugs and constructs full topic URLs
- Parses individual topic pages to extract thread content
- Handles the migration from discourse.ros.org to discourse.openrobotics.org

**Data extracted:**
- `title`: Thread/post title
- `thread_contents`: Main thread content paragraphs
- `thread_details`: Additional details from list items
- `url`: Thread URL

**Output:** JSON data saved to `/data`

---

### 1.5 WikiStats
**Purpose:** Extracts statistical metadata about ROS packages from ROS Index API.

**How it works:**
- Fetches package data from ROS Index API
- Extracts metadata fields: URL, last commit time, and authors
- Processes author data (handles both list and string formats)
- Simple one-pass extraction without following links

**Data extracted:**
- `url`: Package URL
- `time`: Last commit timestamp
- `user`: Package authors (comma-separated)

**Output:** JSON data saved to `/data`

---

### 1.6 SOStats (Stack Overflow Stats)
**Purpose:** Extracts user information for questions already collected by SOWebCrawler.

**How it works:**
- Reads existing Stack Overflow data from JSON file
- Extracts question IDs from URLs
- Uses Stack Exchange API to fetch owner/author information for each question
- Adds user display names to existing question data

**Data extracted:**
- `url`: Question URL
- `user`: Display name of question author

**Output:** JSON data saved to `/data`

---

### 1.7 ROSAStats (ROS Answers Stats)
**Purpose:** Extracts user information for questions already collected by ROSAWebCrawler.

**How it works:**
- Reads existing ROS Answers data from JSON file
- Extracts question IDs from URLs
- Uses Stack Exchange API in batch mode (up to 100 questions per request)
- Fetches owner information for questions
- Tracks missing/deleted questions

**Data extracted:**
- `url`: Question URL
- `user`: Display name of question author

**Output:** JSON data saved to `/data`

---

### 1.8 WikiURL
**Purpose:** Simple URL extractor for ROS package URLs from ROS Index.

**How it works:**
- Fetches package data from ROS Index API
- Extracts only the URL field from each package entry
- Minimal processing - just URL extraction

**Data extracted:**
- `urls`: Package URL

**Output:** JSON data saved to `/data`

---

## Part 2: Git Scrapers Analysis (`/git_scraper`)

The git scraper directory contains scripts that extract data from Git repositories (both local clones and via APIs).

### 2.1 git_data_extractor.py
**Purpose:** Extracts source code comments and markdown documentation from cloned Git repositories.

**How it works:**
- Iterates through all repositories in `git_repos/` directory
- For each repository:
  - Scans for `.cpp` and `.py` source files
  - Extracts C++ comments (`//` and `/* */`) from `.cpp` files
  - Extracts Python comments (`#`) from `.py` files (excluding preprocessor directives)
  - Extracts full contents of `.md` (markdown) files
  - Organizes data by file name
- Creates JSON objects with repository name, file names, and extracted content

**Data extracted:**
- `git_repo_name`: Repository name
- `code_comments_file_names`: List of source files with comments
- `md_file_names`: List of markdown files
- `md_contents`: Full contents of markdown files (keyed by file path)
- `code_comments_c++`: C++ comments organized by file name
- `code_comments_python`: Python comments organized by file name

**Output:** `data2/git_repos1_data.json`

---

### 2.2 commit_extractor.py
**Purpose:** Extracts commit history (messages, hashes, dates) from cloned Git repositories.

**How it works:**
- Reads repository list from `Repos_all.csv`
- For each repository in `git_repos/`:
  - Validates that repository exists and is a valid Git repo
  - Uses `pydriller` library to traverse all commits
  - Extracts commit messages, commit hashes, and commit dates
  - Gets repository URL from Git remote
  - Creates a dictionary mapping commit hashes to commit messages

**Data extracted:**
- `repo_name`: Repository name
- `url`: Repository remote URL
- `commit_info`: List of dictionaries containing commit hash → commit message mappings

**Output:** `data2/commit_data.json`

---

### 2.3 GitHubWebCrawler (Open Issues)
**Purpose:** Extracts open issues from GitHub repositories using GitHub API.

**How it works:**
- Reads repository URLs from `Repos_all.csv`
- Filters for GitHub repositories and checks if they exist in `git_repos/`
- Uses GitHub API to fetch open issues (filters out pull requests)
- Implements pagination to get all issues
- Parses markdown in issue bodies to extract:
  - Code blocks (```code``` and `code`)
  - Blockquotes (> text)
  - Lists (bulleted and numbered)
  - Regular paragraphs
- Handles rate limiting (429 errors) with automatic retry
- Supports resume capability (tracks processed repositories)

**Data extracted:**
- `url`: Issue URL
- `issue_title`: Issue title
- `issue_status`: "Open"
- `posted_on`: Creation timestamp
- `issue_contents`: Paragraph text from issue body
- `issue_code`: Code snippets from issue
- `issue_quotes`: Blockquotes from issue
- `contents_details`: Long list items from issue
- `contents_details_more`: Short list items from issue

**Output:** `data2/github-open-issues_data.json`

---

### 2.4 GitClosedIssuesWebCrawler
**Purpose:** Extracts closed issues from GitHub repositories using GitHub API.

**How it works:**
- Same mechanism as GitHubWebCrawler but fetches closed issues
- Uses `state=closed` parameter in API requests
- Same markdown parsing and data extraction logic
- Tracks processed repositories to avoid duplicates

**Data extracted:**
- Same fields as open issues, but with `issue_status`: "Closed"

**Output:** `data2/github-closed-issues_data.json`

---

### 2.5 GitOpenPRWebCrawler
**Purpose:** Extracts open pull requests from GitHub repositories using GitHub API.

**How it works:**
- Reads repository URLs from CSV and validates existence
- Uses GitHub API to fetch open pull requests
- For each PR, fetches associated comments via separate API call
- Parses markdown in PR body and comments
- Extracts code, quotes, lists, and paragraphs
- Handles rate limiting and implements resume capability

**Data extracted:**
- `url`: PR URL
- `pr_title`: Pull request title
- `username`: PR author username
- `username_url`: PR author profile URL
- `issue_status`: "Open"
- `posted_on`: Creation timestamp
- `pr_contents`: Paragraph text from PR body
- `pr_code`: Code snippets from PR
- `pr_quotes`: Blockquotes from PR
- `pr_details`: Long list items
- `pr_details_more`: Short list items
- `pr_comments`: Comments on the PR

**Output:** `data2/github-open-pr_data.json`

---

### 2.6 GitClosedPRWebCrawler
**Purpose:** Extracts closed pull requests from GitHub repositories using GitHub API.

**How it works:**
- Same mechanism as GitOpenPRWebCrawler but fetches closed PRs
- Uses `state=closed` parameter in API requests
- Same data extraction and comment fetching logic

**Data extracted:**
- Same fields as open PRs, but with `issue_status`: "Closed"

**Output:** `data2/github-closed-pr_data.json`

---

### 2.7 bitbucket_pr_extractor.py
**Purpose:** Extracts declined pull requests from specific BitBucket repositories using BitBucket API.

**How it works:**
- Uses hardcoded list of 8 BitBucket repository API URLs
- Fetches declined pull requests via BitBucket API
- For each PR, extracts:
  - Title, description, author, creation date
  - PR number and comments
- Makes additional API calls to fetch comments for each PR
- Handles deleted users (sets author as "former author")

**Data extracted:**
- `url`: PR URL
- `pr_title`: Pull request title
- `username`: PR author display name
- `status`: "Declined"
- `posted_on`: Creation timestamp
- `pr_contents`: PR description
- `pr_comments`: List of comment texts

**Output:** `data2/bitbucket_pr_data.json`

---

## Data Flow Summary

### Web Crawlers → `/data`
1. WikiCrawler → Package documentation
2. SOWebCrawler → Stack Overflow Q&A
3. ROSAWebCrawler → ROS Answers Q&A
4. ROSDWebCrawler → ROS Discourse threads
5. WikiStats → Package metadata
6. SOStats → Stack Overflow user info
7. ROSAStats → ROS Answers user info
8. WikiURL → Package URLs

### Git Scrapers → `/git_scraper/data2`
1. git_data_extractor.py → Source code comments & markdown
2. commit_extractor.py → Commit history
3. GitHubWebCrawler → GitHub open issues
4. GitClosedIssuesWebCrawler → GitHub closed issues
5. GitOpenPRWebCrawler → GitHub open PRs
6. GitClosedPRWebCrawler → GitHub closed PRs
7. bitbucket_pr_extractor.py → BitBucket declined PRs

---

## Technical Notes

- **Web Crawlers:** Built with Scrapy framework, use APIs where possible to avoid scraping issues
- **Git Scrapers:** Mix of direct file system access (for cloned repos) and API calls (for GitHub/BitBucket)
- **Rate Limiting:** All API-based scrapers implement rate limiting and retry logic
- **Resume Capability:** Most scrapers can resume from previous runs by tracking processed items
- **Data Format:** All output is JSON, with some files using newline-delimited JSON format

