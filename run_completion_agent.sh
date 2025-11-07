#!/bin/bash
# Prime Spark AI - Enhanced Completion Agent Launcher
# This script runs the autonomous completion agent with proper environment setup

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                            ║${NC}"
echo -e "${BLUE}║    Prime Spark AI - Autonomous Completion Agent           ║${NC}"
echo -e "${BLUE}║    Intelligent Project Completion System                  ║${NC}"
echo -e "${BLUE}║                                                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running from project root
if [ ! -f "enhanced_completion_agent.py" ]; then
    echo -e "${RED}Error: Please run this script from the prime-spark-ai project root${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${BLUE}→ Python Version:${NC} $PYTHON_VERSION"

# Check if required Python packages are installed
echo -e "${BLUE}→ Checking dependencies...${NC}"

missing_deps=()

python3 -c "import psutil" 2>/dev/null || missing_deps+=("psutil")
python3 -c "import asyncio" 2>/dev/null || true  # Built-in

if [ ${#missing_deps[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Missing dependencies: ${missing_deps[*]}${NC}"
    echo -e "${BLUE}→ Installing missing dependencies...${NC}"
    pip3 install --user "${missing_deps[@]}"
fi

# Create completion reports directory
mkdir -p completion_reports

echo -e "${GREEN}✅ Environment ready${NC}"
echo ""

# Run options
if [ "$1" == "--dry-run" ]; then
    echo -e "${YELLOW}→ Dry-run mode: Analyzing what would be done...${NC}"
    python3 enhanced_completion_agent.py --dry-run
elif [ "$1" == "--phase" ]; then
    if [ -z "$2" ]; then
        echo -e "${RED}Error: Please specify phase number (1-4)${NC}"
        echo "Usage: $0 --phase [1-4]"
        exit 1
    fi
    echo -e "${BLUE}→ Running Phase $2 only...${NC}"
    python3 enhanced_completion_agent.py --phase "$2"
else
    echo -e "${BLUE}→ Running all phases...${NC}"
    echo -e "${YELLOW}This may take several minutes${NC}"
    echo ""

    # Run the agent
    python3 enhanced_completion_agent.py

    EXIT_CODE=$?

    echo ""
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║                                                            ║${NC}"
        echo -e "${GREEN}║    ✅ Completion Agent Finished Successfully!             ║${NC}"
        echo -e "${GREEN}║                                                            ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${BLUE}📄 Reports Generated:${NC}"
        echo -e "  • Markdown: ${GREEN}completion_reports/enhanced_completion_report.md${NC}"
        echo -e "  • Dashboard: ${GREEN}completion_reports/dashboard.html${NC}"
        echo -e "  • Logs: ${GREEN}enhanced_completion_agent.log${NC}"
        echo ""
        echo -e "${BLUE}💡 Next Steps:${NC}"
        echo "  1. Review the completion report"
        echo "  2. Open dashboard in browser: file://$(pwd)/completion_reports/dashboard.html"
        echo "  3. Check generated code in prime_spark/ and docs/"
        echo "  4. Run tests: pytest tests/"
        echo ""
    else
        echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║                                                            ║${NC}"
        echo -e "${RED}║    ❌ Completion Agent Failed                             ║${NC}"
        echo -e "${RED}║                                                            ║${NC}"
        echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${RED}Check logs for details: enhanced_completion_agent.log${NC}"
        exit $EXIT_CODE
    fi
fi
