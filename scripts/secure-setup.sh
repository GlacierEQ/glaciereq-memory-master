#!/usr/bin/env bash
set -euo pipefail

echo "🔒 SECURE SETUP - You-Only Configuration"
echo "======================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Step 1: Verify .env is git-ignored
echo "🔍 Checking .env security..."

if git check-ignore -q .env 2>/dev/null; then
    echo -e "  ${GREEN}✅ .env is properly git-ignored${NC}"
else
    echo -e "  ${YELLOW}⚠️  Adding .env to .gitignore${NC}"
    echo ".env" >> .gitignore
    echo "*.key" >> .gitignore
    echo "*.pem" >> .gitignore
    echo "secrets/" >> .gitignore
    git add .gitignore
    git commit -m "🔒 Add security patterns to .gitignore"
fi

# Step 2: Create secure .env
echo "🔐 Creating secure environment configuration..."

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "  ${GREEN}✅ .env created from template${NC}"
else
    echo -e "  ${YELLOW}⚠️  .env already exists${NC}"
fi

# Step 3: Security recommendations
echo "📋 Security Setup Instructions:"
echo "1. Edit .env file (NEVER COMMIT):"
echo "   - Add your MEM0_API_KEY"
echo "   - Add your SUPERMEMORY_API_KEY"
echo "   - Optionally set NEO4J_PASSWORD (default: password)"
echo ""
echo "2. For maximum security, also add:"
echo "   - API_BIND_LOCAL=true (localhost-only access)"
echo "   - API_KEY=your_secret_key (require authentication)"
echo "   - UVICORN_HOST=127.0.0.1 (loopback binding)"
echo ""

# Step 4: Generate secure API key if requested
read -p "Generate a secure API key for local authentication? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    SECURE_API_KEY=$(openssl rand -hex 32)
    echo "🔑 Generated secure API key (64 chars)"
    echo "   Add this to .env:"
    echo "   API_KEY=$SECURE_API_KEY"
    echo "   API_BIND_LOCAL=true"
    echo ""
    echo "   Then use this header for API calls:"
    echo "   -H 'X-API-Key: $SECURE_API_KEY'"
fi

# Step 5: Pre-flight safety check
echo "🛡️  Pre-deployment safety check:"

# Check for staged secrets
if git diff --name-only --cached | grep -E '\.env|key|secret|token' >/dev/null; then
    echo -e "  ${RED}❌ DANGER: Secrets found in staged changes!${NC}"
    echo "     Run: git reset HEAD"
else
    echo -e "  ${GREEN}✅ No secrets staged for commit${NC}"
fi

# Check .env exists and has keys
if [ -f ".env" ]; then
    if grep -q "MEM0_API_KEY=" .env && ! grep -q "MEM0_API_KEY=$" .env; then
        echo -e "  ${GREEN}✅ MEM0_API_KEY configured${NC}"
    else
        echo -e "  ${YELLOW}⚠️  MEM0_API_KEY needs configuration${NC}"
    fi
    
    if grep -q "SUPERMEMORY_API_KEY=" .env && ! grep -q "SUPERMEMORY_API_KEY=$" .env; then
        echo -e "  ${GREEN}✅ SUPERMEMORY_API_KEY configured${NC}"
    else
        echo -e "  ${YELLOW}⚠️  SUPERMEMORY_API_KEY needs configuration${NC}"
    fi
fi

echo ""
echo "🚀 Ready for secure deployment!"
echo "   Next: bash scripts/deploy-and-validate.sh"
