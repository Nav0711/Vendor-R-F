#!/bin/bash
# run_test_device.sh
# Run this from the vendorlens-proto root directory.

echo "Setting up testing environment for VendorLens..."

# Ensure we are in the right directory
if [ ! -f "main.py" ]; then
    echo "Error: Please run this script from the vendorlens-proto root directory."
    echo "Usage: ./scripts/run_test_device.sh"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt
pip install openpyxl pandas

# Ensure DB is fresh for testing
if [ -f "vendorlens.db" ]; then
    echo "Removing old database to ensure fresh schema..."
    rm vendorlens.db
fi

# Check for API Keys
if grep -q "ANTHROPIC_API_KEY=$" .env; then
    echo "======================================================"
    echo "WARNING: ANTHROPIC_API_KEY is empty in .env"
    echo "The test will fall back to mocked LLM findings and won't"
    echo "test the new Indian TSP risk rules."
    echo "======================================================"
fi

echo "Running the integration test..."
python scripts/test_sandbox_integration.py
