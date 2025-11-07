#!/bin/bash
# Prime Spark Notion Bridge Agent Deployment Script
# Deploys and configures the bridge between Claude Code and Notion workspace

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_FILE="$SCRIPT_DIR/agents/notion_bridge_agent.py"
CONFIG_FILE="$SCRIPT_DIR/.env"
LOG_DIR="$SCRIPT_DIR/logs"
VENV_DIR="$SCRIPT_DIR/venv"

# Functions
log() {
  echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
  echo -e "${RED}[ERROR]${NC} $1"
  exit 1
}

warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

print_banner() {
  cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║        PRIME SPARK NOTION BRIDGE AGENT DEPLOYMENT            ║
║                                                               ║
║   Connect Claude Code (local) with Notion workspace          ║
║   for seamless project documentation and collaboration       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
}

check_prerequisites() {
  log "Checking prerequisites..."

  # Check Python
  if ! command -v python3 &> /dev/null; then
    error "Python 3 is not installed"
  fi

  # Check pip
  if ! command -v pip3 &> /dev/null; then
    error "pip3 is not installed"
  fi

  log "✓ Prerequisites satisfied"
}

setup_environment() {
  log "Setting up Python environment..."

  # Create virtual environment if it doesn't exist
  if [ ! -d "$VENV_DIR" ]; then
    info "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
  fi

  # Activate virtual environment
  source "$VENV_DIR/bin/activate"

  # Install/upgrade pip
  pip install --upgrade pip &> /dev/null

  # Install required packages
  info "Installing dependencies..."
  pip install notion-client requests python-dotenv &> /dev/null

  log "✓ Environment setup complete"
}

create_directories() {
  log "Creating necessary directories..."

  mkdir -p "$LOG_DIR"
  mkdir -p "$SCRIPT_DIR/cache/notion"
  mkdir -p "$SCRIPT_DIR/docs/notion_sync"

  log "✓ Directories created"
}

configure_notion_api() {
  log "Configuring Notion API..."

  if [ -f "$CONFIG_FILE" ]; then
    if grep -q "NOTION_API_KEY" "$CONFIG_FILE"; then
      info "Notion API key already configured in .env file"
      return
    fi
  fi

  cat << EOF

${YELLOW}═══════════════════════════════════════════════════════════════${NC}
${YELLOW}              NOTION API INTEGRATION SETUP                      ${NC}
${YELLOW}═══════════════════════════════════════════════════════════════${NC}

To connect Claude Code with your Notion workspace, follow these steps:

1. Create a Notion Integration:
   ${BLUE}→ Go to: https://www.notion.so/my-integrations${NC}
   ${BLUE}→ Click "New integration"${NC}
   ${BLUE}→ Name it: "Prime Spark Bridge Agent"${NC}
   ${BLUE}→ Select your workspace${NC}
   ${BLUE}→ Set capabilities: Read content, Update content, Insert content${NC}
   ${BLUE}→ Click "Submit"${NC}

2. Copy the Integration Token:
   ${BLUE}→ Copy the "Internal Integration Token" (starts with secret_...)${NC}

3. Share your Notion pages with the integration:
   ${BLUE}→ Open your Prime Spark AI page in Notion${NC}
   ${BLUE}→ Click "..." (three dots) in the top right${NC}
   ${BLUE}→ Click "Add connections"${NC}
   ${BLUE}→ Select "Prime Spark Bridge Agent"${NC}
   ${BLUE}→ Click "Confirm"${NC}

${YELLOW}═══════════════════════════════════════════════════════════════${NC}

EOF

  read -p "Have you completed the setup above? (yes/no): " setup_complete

  if [ "$setup_complete" != "yes" ]; then
    warn "Please complete the Notion integration setup and run this script again."
    exit 0
  fi

  read -sp "Enter your Notion Integration Token: " notion_token
  echo ""

  if [ -z "$notion_token" ]; then
    error "No token provided"
  fi

  # Add to .env file
  if [ ! -f "$CONFIG_FILE" ]; then
    touch "$CONFIG_FILE"
  fi

  echo "NOTION_API_KEY=$notion_token" >> "$CONFIG_FILE"

  log "✓ Notion API key configured"
}

make_executable() {
  log "Making bridge agent executable..."

  chmod +x "$AGENT_FILE"

  log "✓ Bridge agent is executable"
}

test_connection() {
  log "Testing Notion connection..."

  # Source environment variables
  if [ -f "$CONFIG_FILE" ]; then
    export $(cat "$CONFIG_FILE" | grep -v '^#' | xargs)
  fi

  # Activate venv and run test
  source "$VENV_DIR/bin/activate"

  if python3 "$AGENT_FILE"; then
    log "✓ Bridge agent connected successfully!"
  else
    warn "Connection test failed. Check your API key and integration setup."
  fi
}

create_systemd_service() {
  log "Would you like to create a systemd service for the bridge agent?"

  read -p "Create systemd service? (yes/no): " create_service

  if [ "$create_service" != "yes" ]; then
    info "Skipping systemd service creation"
    return
  fi

  cat > /tmp/notion-bridge.service << EOF
[Unit]
Description=Prime Spark Notion Bridge Agent
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$SCRIPT_DIR
Environment="PATH=$VENV_DIR/bin:/usr/local/bin:/usr/bin"
EnvironmentFile=$CONFIG_FILE
ExecStart=$VENV_DIR/bin/python3 $AGENT_FILE
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

  sudo cp /tmp/notion-bridge.service /etc/systemd/system/
  sudo systemctl daemon-reload

  log "✓ Systemd service created"
  info "To start the service: sudo systemctl start notion-bridge"
  info "To enable on boot: sudo systemctl enable notion-bridge"
}

print_usage_instructions() {
  cat << EOF

${GREEN}═══════════════════════════════════════════════════════════════${NC}
${GREEN}              DEPLOYMENT COMPLETE!                              ${NC}
${GREEN}═══════════════════════════════════════════════════════════════${NC}

The Notion Bridge Agent is now deployed and ready to use!

${BLUE}Basic Usage:${NC}

1. Test the connection:
   ${YELLOW}cd $SCRIPT_DIR${NC}
   ${YELLOW}source venv/bin/activate${NC}
   ${YELLOW}python3 agents/notion_bridge_agent.py${NC}

2. Use in Python scripts:
   ${YELLOW}from agents.notion_bridge_agent import NotionBridgeAgent${NC}
   ${YELLOW}agent = NotionBridgeAgent()${NC}
   ${YELLOW}pages = agent.get_prime_spark_pages()${NC}

3. Search your workspace:
   ${YELLOW}results = agent.search_workspace("your query")${NC}

4. Sync pages to local markdown:
   ${YELLOW}agent.sync_to_local(page_id)${NC}

${BLUE}Files Created:${NC}
   • Bridge Agent: $AGENT_FILE
   • Configuration: $CONFIG_FILE
   • Logs: $LOG_DIR/notion_bridge.log
   • Cache: $SCRIPT_DIR/cache/notion/
   • Synced Docs: $SCRIPT_DIR/docs/notion_sync/

${BLUE}Next Steps:${NC}
   1. Claude Code can now access your Notion workspace
   2. Keep your Notion pages updated with project info
   3. The bridge agent will sync changes automatically
   4. Share pages with the integration to make them accessible

${GREEN}═══════════════════════════════════════════════════════════════${NC}

EOF
}

# Main deployment flow
main() {
  print_banner

  log "Starting Notion Bridge Agent deployment..."

  check_prerequisites
  create_directories
  setup_environment
  configure_notion_api
  make_executable
  test_connection
  create_systemd_service
  print_usage_instructions

  log "Deployment completed successfully! 🚀"
}

# Run main function
main "$@"
