#!/bin/bash

# Script to connect to GitHub Codespace, create test scripts, and run tests
# Usage: ./codespace_test.sh
# SSH connection details
HOST="cs.organic-space-succotash-wwgpr95rg4q25r5p.dev"
PORT="22"
USER="codespace"
SSH_KEY="$HOME/.ssh/codespaces.auto"

echo "Connecting to: $USER@$HOST:$PORT with key $SSH_KEY"

# Function to run SSH commands
run_ssh() {
    ssh -o ProxyCommand="/data/data/com.termux/files/usr/bin/gh cs ssh -c organic-space-succotash-wwgpr95rg4q25r5p --stdio -- -i $SSH_KEY" codespace@cs.organic-space-succotash-wwgpr95rg4q25r5p.dev "$1"
    ssh -o ProxyCommand="/data/data/com.termux/files/usr/bin/gh cs ssh -c organic-space-succotash-wwgpr95rg4q25r5p --stdio -- -i $SSH_KEY" codespace@cs.organic-space-succotash-wwgpr95rg4q25r5p.dev "$1"
}

# Step 1: Create test directory and basic test files
echo "Creating test scripts in codespace..."
run_ssh "mkdir -p /workspaces/manga-atriuum/tests"

# Create a simple test file
run_ssh "cat > /workspaces/manga-atriuum/tests/test_app.py << 'EOF'
from streamlit.testing.v1 import AppTest

def test_app_loads():
    at = AppTest.from_file('streamlit_app.py').run()
    assert 'Manga Lookup Tool' in str(at.main[0].value)  # Basic check for title

def test_series_input():
    at = AppTest.from_file('streamlit_app.py').run()
    # Simulate input (adjust as needed)
    text_input = at.text_input[0]  # First text input
    text_input.input('Naruto').run()
    assert at.session_state.pending_series_name == 'Naruto'
EOF"

# Create another test file
run_ssh "cat > /workspaces/manga-atriuum/tests/test_example.py << 'EOF'
def test_example():
    assert 1 + 1 == 2
EOF"

# Step 2: Install dependencies (if needed)
echo "Ensuring dependencies are installed..."
run_ssh "cd /workspaces/manga-atriuum && pip install -r requirements.txt || pip install streamlit pytest"

# Step 3: Run tests
echo "Running tests..."
run_ssh "cd /workspaces/manga-atriuum && pytest tests/ -v"

echo "Done! Check output above for test results."
