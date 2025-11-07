# Untitled_19

*Synced from Notion*

🔗 [View in Notion](https://notion.so/2a3c730ec2c881a6af8bd5e07b10b455)

---

# ⚡ Prime Spark Quick Start

Your essential daily actions and quick access guide

## 🎯

## Daily Essentials

### Morning Ritual

### Quick Access Links

• Infrastructure Dashboard

• :

• http://46.202.194.118:9999

• Open-WebUI (AI Chat)

• :

• http://primecore1.online:8080

• N8N Workflows

• :

• http://primecore1.online:8085

• Claude Code Services

• :

• 🤖 Claude Code Services

## 🚀

## Common Actions

### 🤖 Working with AI Agents

Chat with AI:

1. Open Open-WebUI:

1. http://primecore1.online:8080

1. Select model (mistral:7b for general, codestral:22b for coding)

1. Start conversation

Run Automation:

1. Open N8N:

1. http://primecore1.online:8085

1. Find workflow or create new

1. Execute or schedule

### 💻 Deploy New Code/MCP

From iPhone (Our Workflow):

1. Create in Claude chat

1. I write to Claude Code Services in Notion

1. Review on iPhone Notion app

1. SSH to Pi: Run

1. ~/

1. prime-spark-sync.sh

1. Deployed! ✅

Manual Deploy to VPS:

```bash
ssh root@46.202.194.118
cd /root/[stack-name]
docker-compose up -d
```

### 📊 Check System Status

VPS Health:

```bash
ssh root@46.202.194.118
docker ps
df -h
free -h
```

Pi 5 Health:

```bash
ssh pi@[pi-ip]
docker ps
vcgencmd measure_temp
```

Dashboard:

• Visual status:

• http://46.202.194.118:9999

### 🔄 Restart Services

Individual Container:

```bash
docker restart [container-name]
```

Full Stack:

```bash
cd /root/[stack-directory]
docker-compose restart
```

All Stacks:

```bash
/root/scripts/start-all-stacks.sh
```

## 📝

## Quick Note Taking

### Capture Ideas:

• Journal

• :

• Untitled

• Flow Pages

• :

• Untitled

• Vision Alchemist

• : For big creative sparks

### Track Tasks:

• To-Do List

• :

• Prime Spark AI To Do list

• Micro Actions

• :

• Untitled

## 🎨

## Content Creation

Quick Workflow:

1. Idea → Vision Alchemist (agent)

1. Draft → Open-WebUI with Claude

1. Schedule → Multi-Platform Content Calendar

1. Automate → N8N for posting

Resources:

• Content Calendar

• :

• Untitled

• Marketing Content

• :

• Untitled

## 🔧

## Troubleshooting

### Service Won't Start:

```bash
# Check logs
docker logs [container-name]

# Check if port is in use
sudo lsof -i :[port-number]

# Restart Docker
sudo systemctl restart docker
```

### Can't Access Service:

1. Check container is running:

1. docker ps

1. Verify port mapping in docker-compose.yml

1. Check firewall rules

1. Test from VPS:

1. curl

1. localhost

1. :[port]

### Out of Space:

```bash
# Clean Docker
docker system prune -a

# Check disk usage
df -h
du -sh /root/*
```

## 📚

## Learning Resources

Documentation:

• Infrastructure Hub

• :

• 📡 Prime Spark Infrastructure Hub

• Site Map

• :

• Prime Spark AI - Site Map

• Road Map

• :

• Untitled

Agent Guides:

• Spark Prime, Pulse, Heartforge, Arkitect, Vision Alchemist, Signal Weaver, Sentinel, Echo

## ⚡

## Power User Shortcuts

### SSH Aliases (Add to ~/.ssh/config):

```javascript
Host vps
  HostName 46.202.194.118
  User root
  
Host pi
  HostName [pi-ip]
  User pi
```

### Bash Aliases (Add to ~/.bashrc):

```bash
alias pslogs='docker logs -f prime-spark-live'
alias psrestart='cd /root/prime-spark-live && docker-compose restart'
alias psstatus='docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
```

## 🎯

## Weekly Checklist