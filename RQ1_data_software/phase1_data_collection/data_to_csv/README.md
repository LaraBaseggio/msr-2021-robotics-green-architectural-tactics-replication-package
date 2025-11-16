# RQ1 Phase 1: Data Collection to CSV Conversion

This directory contains scripts to process JSON data collected by web scrapers and convert it to CSV format for analysis. MongoDB serves as intermediate storage for some data sources.

## Overview

The data processing pipeline follows this flow:
```
Scraped JSON Files → MongoDB (intermediate storage) → CSV Files (for analysis)
```

## Prerequisites

- Python 3.x
- MongoDB instance (local or cloud)
- Required Python packages:
  ```bash
  pip install pymongo csv json itertools collections
  ```

## Directory Structure

```
RQ1_data_software/phase1_data_collection/data_to_csv/
├── get_prs.py              # Load GitHub PRs into MongoDB
├── get_rosa.py             # Load ROS Answers into MongoDB
├── git-prs_to_csv.py       # Convert GitHub PRs to CSV
├── git-issues_to_csv.py    # Convert GitHub Issues to CSV
├── so_to_csv.py            # Convert Stack Overflow to CSV
├── rosa_to_csv.py          # Convert ROS Answers to CSV
├── rosd_to_csv.py          # Convert ROS Discourse to CSV
├── repo_to_csv.py          # Convert Repository data to CSV
├── data/                   # Output CSV files
└── Repos_all.csv          # Input repository list
```

## Input Files Required

Ensure these files exist from your scraping phase:

```
├── git_scraper/data2/
│   ├── github-open-pr_data.json      # Open pull requests
│   ├── github-closed-pr_data.json    # Closed pullrequests  
│   ├── github-closed-issues_data.json # Closed issues
│   └── git_repos1_data.json          # Repository metadata
├── data/
│   ├── stackoverflow_new_data.json   # Stack Overflow posts
│   ├── rosa_new_data.json            # ROS Answers posts
│   └── rosd_new_data.json            # ROS Discourse posts
└── Repos_all.csv                     # Repository list
```

## MongoDB Setup

Update the MongoDB connection string in relevant scripts:

````python
# In get_prs.py and get_rosa.py
client = MongoClient("mongodb+srv://yourUser:yourPassword@yourCluster.mongodb.net/data_phase1?ssl=true&ssl_cert_reqs=CERT_NONE")
db = client.data_phase1