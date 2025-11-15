#!/bin/bash

# Script to run git_data_extractor.py and commit_extractor.py in parallel using tmux
# Usage: ./run_extractors_parallel.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo "Error: tmux is not installed. Please install it first:"
    echo "  sudo apt-get install tmux  # Ubuntu/Debian"
    echo "  sudo yum install tmux      # CentOS/RHEL"
    exit 1
fi

# Check if git_repos directory exists
if [ ! -d "git_repos" ]; then
    echo "Error: git_repos directory not found!"
    echo "Please run clone_repos.py first."
    exit 1
fi

# Create output directories if they don't exist
mkdir -p data data2

echo "Setting up tmux sessions for parallel execution..."
echo ""

# Kill existing sessions if they exist (optional - uncomment if you want to restart)
# tmux kill-session -t git_data_extractor 2>/dev/null
# tmux kill-session -t commit_extractor 2>/dev/null

# Check if virtual environment exists
if [ -d "$SCRIPT_DIR/.venv" ]; then
    VENV_ACTIVATE="source $SCRIPT_DIR/.venv/bin/activate && "
    echo "Using virtual environment: $SCRIPT_DIR/.venv"
else
    VENV_ACTIVATE=""
    echo "Warning: No virtual environment found. Make sure required packages are installed."
fi

# Create tmux session for git_data_extractor.py
echo "Creating tmux session 'git_data_extractor'..."
tmux new-session -d -s git_data_extractor -c "$SCRIPT_DIR" \
    "${VENV_ACTIVATE}python3 git_data_extractor.py; echo ''; echo 'Press Enter to close this window...'; read"

# Create tmux session for commit_extractor.py
echo "Creating tmux session 'commit_extractor'..."
tmux new-session -d -s commit_extractor -c "$SCRIPT_DIR" \
    "${VENV_ACTIVATE}python3 commit_extractor.py; echo ''; echo 'Press Enter to close this window...'; read"

echo ""
echo "Both scripts are now running in parallel in tmux sessions!"
echo ""
echo "To view the sessions:"
echo "  tmux attach -t git_data_extractor    # View git_data_extractor progress"
echo "  tmux attach -t commit_extractor      # View commit_extractor progress"
echo ""
echo "To detach from a session:"
echo "  Press Ctrl+B, then D"
echo ""
echo "To list all sessions:"
echo "  tmux ls"
echo ""
echo "To kill a session:"
echo "  tmux kill-session -t git_data_extractor"
echo "  tmux kill-session -t commit_extractor"
echo ""
echo "To kill all sessions:"
echo "  tmux kill-session -t git_data_extractor; tmux kill-session -t commit_extractor"
echo ""

# Optionally attach to one of the sessions
read -p "Would you like to attach to git_data_extractor session now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    tmux attach -t git_data_extractor
fi

