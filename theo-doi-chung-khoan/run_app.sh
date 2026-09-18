#!/bin/bash
# Streamlit App Launcher - Theo dõi chứng khoán
# Usage: ./run_app.sh

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}📈 Theo dõi chứng khoán${NC}"
echo -e "${BLUE}Streamlit App Launcher${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found!${NC}"
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}\n"
fi

# Activate venv
echo -e "${BLUE}Activating virtual environment...${NC}"
source .venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}\n"

# Check if database exists
if [ ! -f "data/portfolio.db" ]; then
    echo -e "${YELLOW}⚠️  Database not found!${NC}"
    echo "Setting up database..."
    python3 setup_database.py
    echo ""
fi

# Run validation tests
echo -e "${BLUE}Running validation tests...${NC}"
if python3 test_setup.py; then
    echo -e "${GREEN}✓ All tests passed!${NC}\n"
else
    echo -e "${YELLOW}⚠️  Some tests failed. Trying to continue...${NC}\n"
fi

# Start Streamlit
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🚀 Starting Streamlit app...${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Open your browser to: http://localhost:8501${NC}"
echo -e "${BLUE}Press Ctrl+C to stop the app${NC}"
echo ""

streamlit run app.py
