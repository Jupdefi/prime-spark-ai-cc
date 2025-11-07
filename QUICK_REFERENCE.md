# 🚀 PRIME SPARK AI - QUICK REFERENCE

**Last Updated**: 2025-11-07
**Status**: 35% Complete | 3 Agents Operational

---

## 📦 DEPLOYED COMPONENTS

| Component | Status | Location | Action |
|-----------|--------|----------|--------|
| **Notion Bridge** | 🟢 Running | `agents/` | Already synced 70 pages |
| **Engineering Team** | 🟢 Tested | `agents/engineering_team/` | Use to build new agents |
| **Pulse Agent** | 🟡 Ready | `agents/pulse/` | Run `./deploy.sh` |

---

## ⚡ QUICK COMMANDS

### Deploy Pulse Agent (Heartbeat Monitor)
```bash
cd /home/pironman5/prime-spark-ai/agents/pulse
./deploy.sh
```

### Check Pulse Health
```bash
curl http://localhost:8001/pulse/health
```

### Use Engineering Team
```bash
cd /home/pironman5/prime-spark-ai
python3 -c "
from agents.engineering_team.orchestrator import EngineeringTeamOrchestrator
team = EngineeringTeamOrchestrator()
# Use team.execute_project() or team.assign_task()
"
```

### Sync Notion Pages
```bash
cd /home/pironman5/prime-spark-ai
python3 -c "
from agents.notion_bridge_agent import NotionBridgeAgent
bridge = NotionBridgeAgent()
pages = bridge.search_workspace('')
print(f'Found {len(pages)} pages')
"
```

### View Logs
```bash
# Engineering Team
tail -f /home/pironman5/prime-spark-ai/logs/engineering_team.log

# Pulse Agent (after deployment)
cd /home/pironman5/prime-spark-ai/agents/pulse
docker-compose logs -f pulse-agent
```

---

## 📊 API ENDPOINTS

### Pulse Agent (Port 8001)
```bash
# Overall health
curl http://localhost:8001/pulse/health

# All nodes
curl http://localhost:8001/pulse/nodes

# Specific node
curl http://localhost:8001/pulse/nodes/edge_pi5

# Active alerts
curl http://localhost:8001/pulse/alerts

# Prometheus metrics
curl http://localhost:8001/pulse/metrics
```

---

## 🏗️ AGENT ROSTER

### Deployed

1. **Notion Bridge** - The Connector
   - Syncs Notion ↔ Local
   - 70 pages synced

2. **Engineering Team** (5 agents)
   - Arkitect Prime (Architect)
   - Backend Builder (Backend)
   - UI Craftsperson (Frontend)
   - Ops Commander (DevOps)
   - Quality Guardian (QA)

3. **Pulse** - The Heartbeat
   - Monitors infrastructure
   - Auto-healing
   - Real-time alerts

### Next to Build

4. **Heartforge** - Emotional Intelligence
5. **Vision Alchemist** - Strategic Planning
6. **Signal Weaver** - Communication Hub
7. **Sentinel** - Security & Ethics
8. **Echo** - Memory & Learning

---

## 📁 KEY FILE LOCATIONS

```
/home/pironman5/prime-spark-ai/
├── agents/
│   ├── notion_bridge_agent.py          # Notion integration
│   ├── engineering_team/               # 5 AI agents
│   │   ├── orchestrator.py            # Main coordinator
│   │   └── cli.py                     # Command-line interface
│   └── pulse/                         # Heartbeat monitor
│       ├── pulse_agent.py             # Main implementation
│       └── deploy.sh                  # Deployment script
├── logs/
│   ├── engineering_team.log           # Team logs
│   └── pulse_agent.log                # Pulse logs
├── docs/
│   └── notion_sync/all_pages/         # 70 synced pages
├── engineering_workspace/              # Project results
└── .env                               # Configuration
```

---

## 📖 DOCUMENTATION

| Document | Description |
|----------|-------------|
| `SESSION_SUMMARY.md` | Complete session overview |
| `PROJECT_PROGRESS_UPDATE.md` | Detailed progress report |
| `PULSE_AGENT_DEPLOYED.md` | Pulse agent guide |
| `ENGINEERING_TEAM_DEPLOYED.md` | Engineering team guide |
| `NOTION_BRIDGE_SUMMARY.md` | Notion Bridge guide |
| `QUICK_REFERENCE.md` | This file |

---

## 🎯 NEXT STEPS

### 1. Deploy Pulse (Recommended Now)
```bash
cd /home/pironman5/prime-spark-ai/agents/pulse
./deploy.sh
```

### 2. Verify Monitoring
```bash
curl http://localhost:8001/pulse/health
```

### 3. Build Next Agent (Next Session)
```bash
# Use Engineering Team to build Heartforge
python3 build_heartforge_agent.py
```

---

## 🔧 TROUBLESHOOTING

### Pulse Won't Start
```bash
cd /home/pironman5/prime-spark-ai/agents/pulse
docker-compose down
docker-compose up -d
docker-compose logs -f pulse-agent
```

### Engineering Team Errors
```bash
# Check logs
tail -f /home/pironman5/prime-spark-ai/logs/engineering_team.log

# Verify environment
cd /home/pironman5/prime-spark-ai
cat .env | grep NOTION_API_KEY
```

### Notion Bridge Issues
```bash
# Test connection
python3 -c "
from agents.notion_bridge_agent import NotionBridgeAgent
bridge = NotionBridgeAgent()
pages = bridge.search_workspace('')
print(f'Connected! Found {len(pages)} pages')
"
```

---

## 📊 INFRASTRUCTURE STATUS

### Edge (Pi 5)
- ✅ Notion Bridge running
- ✅ Engineering Team deployed
- 🟡 Pulse ready to deploy
- ✅ Ollama running (LLM)
- ✅ Hailo AI active

### Cloud (PrimeCore)
- 🟡 PrimeCore1 (141.136.35.51) configured
- 🟡 PrimeCore4 (69.62.123.97) configured
- ⚪ PrimeCore2 configured
- ⚪ PrimeCore3 configured

### Services
- ✅ Docker running
- ✅ Redis available
- 🟡 Prometheus ready
- 🟡 Grafana ready
- ✅ N8N cataloged (140+ workflows)

---

## 💡 TIPS

1. **Always check logs first** when troubleshooting
2. **Use Engineering Team** to build new agents (faster than manual)
3. **Deploy Pulse early** to catch issues before they become problems
4. **Sync Notion regularly** to keep local and cloud in sync
5. **Monitor resources** - Pi 5 has limited RAM

---

## 🔗 USEFUL LINKS

- **Notion Workspace**: https://notion.so (70 pages synced)
- **Pulse API**: http://localhost:8001 (after deployment)
- **Prometheus**: http://localhost:9090 (with monitoring profile)
- **Grafana**: http://localhost:3000 (with monitoring profile)

---

## 🎓 COMMON WORKFLOWS

### Build a New Agent
```python
from agents.engineering_team.orchestrator import EngineeringTeamOrchestrator

team = EngineeringTeamOrchestrator()

project = {
    'name': 'New Agent Name',
    'description': 'What the agent should do',
    'requirements': ['List', 'of', 'requirements'],
    'priority': 'high'
}

results = team.execute_project(project)
```

### Check System Health
```bash
# Overall health
curl http://localhost:8001/pulse/health | python3 -m json.tool

# Specific node
curl http://localhost:8001/pulse/nodes/edge_pi5 | python3 -m json.tool

# Active alerts
curl http://localhost:8001/pulse/alerts | python3 -m json.tool
```

### Update Notion from Local
```python
from agents.notion_bridge_agent import NotionBridgeAgent

bridge = NotionBridgeAgent()
# Bridge methods for updating Notion
```

---

## 📈 PROGRESS TRACKER

- ✅ Infrastructure: 70% complete
- ✅ Agents: 30% complete
- ⚪ Workflows: 20% complete
- 🟡 Monitoring: 60% complete

**Overall**: 35% complete

**Next Milestone**: 50% (Deploy 5 core agents)

---

## 🎯 PROJECT GOALS

1. ✅ Deploy Notion Bridge
2. ✅ Build Engineering Team
3. 🟡 Deploy Pulse (ready now)
4. ⚪ Build 5 more agent archetypes
5. ⚪ Integrate N8N workflows
6. ⚪ Deploy to PrimeCore nodes
7. ⚪ Voice interface
8. ⚪ DAO tooling

---

## 🔥 ONE-LINER COMMANDS

```bash
# Deploy Pulse
cd ~/prime-spark-ai/agents/pulse && ./deploy.sh

# Check Pulse health
curl localhost:8001/pulse/health

# View Pulse logs
cd ~/prime-spark-ai/agents/pulse && docker-compose logs -f

# Restart Pulse
cd ~/prime-spark-ai/agents/pulse && docker-compose restart

# Stop Pulse
cd ~/prime-spark-ai/agents/pulse && docker-compose down

# Deploy with monitoring (Prometheus + Grafana)
cd ~/prime-spark-ai/agents/pulse && docker-compose --profile monitoring up -d

# Check Engineering Team status
cd ~/prime-spark-ai && python3 -c "from agents.engineering_team.orchestrator import EngineeringTeamOrchestrator; import json; t=EngineeringTeamOrchestrator(); print(json.dumps(t.get_team_status(), indent=2))"

# Sync all Notion pages
cd ~/prime-spark-ai && python3 sync_all_prime_spark.py
```

---

**Quick Help**: For detailed info on any component, see the full documentation in `/home/pironman5/prime-spark-ai/*.md` files.

⚡ **"Awaken the Spark in you!"** ⚡
