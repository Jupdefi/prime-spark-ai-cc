#!/bin/bash
# Prime Spark AI - VPN Setup Script
# This script sets up WireGuard VPN on edge and cloud nodes

set -e

echo "=================================================="
echo "Prime Spark AI - VPN Infrastructure Setup"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo)${NC}"
    exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo -e "${RED}Cannot detect OS${NC}"
    exit 1
fi

echo -e "${GREEN}Detected OS: $OS${NC}"

# Install WireGuard based on OS
install_wireguard() {
    echo -e "${YELLOW}Installing WireGuard...${NC}"

    case $OS in
        ubuntu|debian|raspbian)
            apt-get update
            apt-get install -y wireguard wireguard-tools
            ;;
        centos|rhel|fedora)
            yum install -y epel-release
            yum install -y wireguard-tools
            ;;
        *)
            echo -e "${RED}Unsupported OS: $OS${NC}"
            exit 1
            ;;
    esac

    echo -e "${GREEN}WireGuard installed successfully${NC}"
}

# Check if WireGuard is installed
if ! command -v wg &> /dev/null; then
    install_wireguard
else
    echo -e "${GREEN}WireGuard is already installed${NC}"
fi

# Enable IP forwarding
echo -e "${YELLOW}Enabling IP forwarding...${NC}"
echo "net.ipv4.ip_forward=1" > /etc/sysctl.d/99-wireguard.conf
sysctl -p /etc/sysctl.d/99-wireguard.conf

# Generate VPN configurations
echo -e "${YELLOW}Generating VPN configurations...${NC}"
cd /home/pironman5/prime-spark-ai
python3 vpn/wireguard_config.py

# Ask which node this is
echo ""
echo "Which node is this?"
echo "1) Control PC (VPN Server)"
echo "2) Spark Agent"
echo "3) PrimeCore1"
echo "4) PrimeCore2"
echo "5) PrimeCore3"
echo "6) PrimeCore4"
read -p "Enter choice [1-6]: " node_choice

case $node_choice in
    1) node_name="control-pc" ;;
    2) node_name="spark-agent" ;;
    3) node_name="primecore1" ;;
    4) node_name="primecore2" ;;
    5) node_name="primecore3" ;;
    6) node_name="primecore4" ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# Copy configuration
config_file="vpn/configs/${node_name}.conf"
if [ ! -f "$config_file" ]; then
    echo -e "${RED}Configuration file not found: $config_file${NC}"
    exit 1
fi

echo -e "${YELLOW}Installing configuration for $node_name...${NC}"
mkdir -p /etc/wireguard
cp "$config_file" /etc/wireguard/wg0.conf
chmod 600 /etc/wireguard/wg0.conf

# Enable and start WireGuard
echo -e "${YELLOW}Enabling and starting WireGuard...${NC}"
systemctl enable wg-quick@wg0
systemctl restart wg-quick@wg0

# Check status
sleep 2
if systemctl is-active --quiet wg-quick@wg0; then
    echo -e "${GREEN}WireGuard is running successfully!${NC}"
    echo ""
    wg show
else
    echo -e "${RED}WireGuard failed to start. Check logs: journalctl -u wg-quick@wg0${NC}"
    exit 1
fi

# Setup firewall rules (if Control PC)
if [ "$node_name" = "control-pc" ]; then
    echo -e "${YELLOW}Setting up firewall rules...${NC}"

    # Check if ufw is installed
    if command -v ufw &> /dev/null; then
        ufw allow 51820/udp
        echo -e "${GREEN}UFW rule added for WireGuard${NC}"
    fi

    # Check if firewalld is installed
    if command -v firewall-cmd &> /dev/null; then
        firewall-cmd --permanent --add-port=51820/udp
        firewall-cmd --reload
        echo -e "${GREEN}Firewalld rule added for WireGuard${NC}"
    fi

    echo ""
    echo -e "${YELLOW}IMPORTANT: Ensure UDP port 51820 is forwarded on your router to this machine${NC}"
fi

echo ""
echo "=================================================="
echo -e "${GREEN}VPN Setup Complete!${NC}"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Run this script on all other nodes"
echo "2. Test connectivity: ping 10.8.0.X"
echo "3. Monitor VPN status: python3 vpn/manager.py status"
echo ""
