#!/bin/bash
# 🚀 APEX BOOTSTRAP v1.0 - GlacierEQ Memory Master
# Phase 1: Infrastructure Bootstrap
# Created: December 1, 2025

set -e

echo "⚡ APEX BOOTSTRAP PROTOCOL INITIATED ⚡"
echo "======================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo -e "${CYAN}"
cat << "EOF"
   _____ _               _           ______ ____  
  / ____| |             (_)         |  ____/ __ \ 
 | |  __| | __ _  ___ _  ___ _ __  | |__ | |  | |
 | | |_ | |/ _` |/ __| |/ _ \ '__| |  __|| |  | |
 | |__| | | (_| | (__| |  __/ |    | |___| |__| |
  \_____|_|\__,_|\___|_|\___|_|    |______\____/ 
                                                  
  APEX MEMORY MASTER - PHASE 1 BOOTSTRAP
EOF
echo -e "${NC}"
echo ""

# Check prerequisites
echo -e "${BLUE}[1/9] Checking prerequisites...${NC}"
command -v docker >/dev/null 2>&1 || { echo -e "${RED}✗ Docker not found${NC}"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo -e "${RED}✗ Docker Compose not found${NC}"; exit 1; }
command -v git >/dev/null 2>&1 || { echo -e "${RED}✗ Git not found${NC}"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}✗ Python3 not found${NC}"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo -e "${RED}✗ npm not found${NC}"; exit 1; }
echo -e "${GREEN}✓ All prerequisites satisfied${NC}"
echo ""

# Clone repositories
echo -e "${BLUE}[2/9] Cloning core repositories...${NC}"
mkdir -p ~/glacier-apex
cd ~/glacier-apex

repos=(
    "glaciereq-memory-master"
    "apex-command-center"
    "FILEBOSS"
)

for repo in "${repos[@]}"; do
    if [ -d "$repo" ]; then
        echo -e "${YELLOW}  → $repo already exists, pulling latest...${NC}"
        cd "$repo" && git pull && cd ..
    else
        echo -e "${CYAN}  → Cloning $repo...${NC}"
        git clone "https://github.com/GlacierEQ/$repo.git"
    fi
done
echo -e "${GREEN}✓ Repositories ready${NC}"
echo ""

# Setup environment
echo -e "${BLUE}[3/9] Configuring environment...${NC}"
cd glaciereq-memory-master
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${YELLOW}  → Created .env file - Please configure API keys${NC}"
else
    echo -e "${GREEN}  → .env already exists${NC}"
fi
echo ""

# Install Python dependencies
echo -e "${BLUE}[4/9] Installing Python dependencies...${NC}"
python3 -m pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ Python dependencies installed${NC}"
echo ""

# Start Docker services
echo -e "${BLUE}[5/9] Starting Docker services...${NC}"
docker-compose up -d
sleep 5
echo -e "${GREEN}✓ Docker services running${NC}"
echo ""

# Health check
echo -e "${BLUE}[6/9] Running health checks...${NC}"
max_retries=30
retry_count=0
while [ $retry_count -lt $max_retries ]; do
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API server healthy${NC}"
        break
    fi
    retry_count=$((retry_count + 1))
    echo -e "${YELLOW}  → Waiting for services... ($retry_count/$max_retries)${NC}"
    sleep 2
done

if [ $retry_count -eq $max_retries ]; then
    echo -e "${RED}✗ Health check timeout${NC}"
    exit 1
fi
echo ""

# Setup Sigma Frontend
echo -e "${BLUE}[7/9] Setting up Sigma Frontend...${NC}"
cd ui/sigma
npm install
echo -e "${GREEN}✓ Sigma frontend dependencies installed${NC}"
cd ../..
echo ""

# Run migrations
echo -e "${BLUE}[8/9] Running Phase 1 migrations...${NC}"
if [ -f scripts/migration-helper.py ]; then
    python3 scripts/migration-helper.py
    echo -e "${GREEN}✓ Migrations complete${NC}"
else
    echo -e "${YELLOW}  → Migration script not found, skipping${NC}"
fi
echo ""

# Final validation
echo -e "${BLUE}[9/9] Running final validation...${NC}"
services=(
    "http://localhost:7474|Neo4j Browser"
    "http://localhost:8080/health|API Server"
    "http://localhost:8000|ChromaDB"
)

all_healthy=true
for service in "${services[@]}"; do
    IFS='|' read -r url name <<< "$service"
    if curl -s "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ $name${NC}"
    else
        echo -e "${RED}  ✗ $name${NC}"
        all_healthy=false
    fi
done
echo ""

# Success banner
if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}"
    cat << "EOF"
╔═══════════════════════════════════════════════════╗
║                                                   ║
║   ✅ PHASE 1 COMPLETE - INFRASTRUCTURE READY ✅   ║
║                                                   ║
╚═══════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    echo ""
    echo -e "${CYAN}🎯 ACCESS POINTS:${NC}"
    echo -e "  ${PURPLE}→${NC} Neo4j Browser:    ${GREEN}http://localhost:7474${NC}"
    echo -e "  ${PURPLE}→${NC} API Server:       ${GREEN}http://localhost:8080${NC}"
    echo -e "  ${PURPLE}→${NC} Memory Status:    ${GREEN}http://localhost:8080/memory/status${NC}"
    echo -e "  ${PURPLE}→${NC} Graph Status:     ${GREEN}http://localhost:8080/graph/status${NC}"
    echo ""
    echo -e "${CYAN}🚀 NEXT STEPS:${NC}"
    echo -e "  ${PURPLE}1.${NC} Launch Sigma UI:  ${YELLOW}cd ui/sigma && npm start${NC}"
    echo -e "  ${PURPLE}2.${NC} View logs:        ${YELLOW}make logs${NC}"
    echo -e "  ${PURPLE}3.${NC} Test memory:      ${YELLOW}make test-memory${NC}"
    echo -e "  ${PURPLE}4.${NC} Phase 2 deploy:   ${YELLOW}make migrate-phase2${NC}"
    echo ""
    echo -e "${GREEN}✨ System operational - Ready for Phase 2! ✨${NC}"
else
    echo -e "${RED}⚠️  Some services failed health check - Review logs${NC}"
    exit 1
fi
