#!/bin/bash
# Simple shell script to run the mortgage lending demo

# Ensure we're in the project root directory
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Run the demo script with any passed arguments
python scripts/run_demo.py "$@"

echo "Demo completed."