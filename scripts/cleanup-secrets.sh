#!/usr/bin/env bash
set -euo pipefail

echo "🧹 SECURITY CLEANUP - Remove Any Exposed Secrets"
echo "==============================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check for common secret patterns in git history
echo "🔍 Scanning for potential secrets in git history..."

SECRET_PATTERNS=(
    "api[_-]?key"
    "secret[_-]?key"
    "access[_-]?token"
    "private[_-]?key"
    "password"
    "sk-proj-"
    "github_pat_"
    "GOCSPX-"
    "AIzaSy"
)

FOUND_SECRETS=false

for pattern in "${SECRET_PATTERNS[@]}"; do
    if git log --all --grep="$pattern" --oneline | head -5; then
        echo -e "  ${YELLOW}⚠️  Potential secrets found in commit messages with pattern: $pattern${NC}"
        FOUND_SECRETS=true
    fi
    
    if git log --all -S"$pattern" --oneline | head -5; then
        echo -e "  ${YELLOW}⚠️  Potential secrets found in commit content with pattern: $pattern${NC}"
        FOUND_SECRETS=true
    fi
done

if [ "$FOUND_SECRETS" = true ]; then
    echo -e "\n${RED}❌ SECURITY ALERT: Potential secrets found in git history${NC}"
    echo "   Recommended actions:"
    echo "   1. Review git log output above"
    echo "   2. If secrets are confirmed, rotate ALL exposed keys"
    echo "   3. Consider git filter-branch or BFG repo cleaner"
    echo "   4. For new repos, start fresh without secret history"
else
    echo -e "  ${GREEN}✅ No obvious secret patterns found in git history${NC}"
fi

# Check current working directory for secret files
echo "\n🔍 Scanning current directory for secret files..."

SECRET_FILES=(
    ".env"
    "*.key"
    "*.pem"
    "*_rsa"
    "*_rsa.pub"
    "secrets.txt"
    "credentials.json"
)

for pattern in "${SECRET_FILES[@]}"; do
    if ls $pattern 2>/dev/null; then
        if git check-ignore -q $pattern 2>/dev/null; then
            echo -e "  ${GREEN}✅ $pattern found but git-ignored${NC}"
        else
            echo -e "  ${RED}❌ DANGER: $pattern found and NOT git-ignored${NC}"
            echo "     Add to .gitignore immediately"
        fi
    fi
done

# Cleanup recommendations
echo "\n🧹 Cleanup Recommendations:"
echo "1. Rotate all API keys from any exposed sources"
echo "2. Remove any downloaded secret files securely:"
echo "   - Linux/macOS: shred -uz filename.pdf"
echo "   - Windows: Use secure delete tool"
echo "3. Clear browser downloads if applicable"
echo "4. Check other devices/conversations for copies"
echo "5. Update .gitignore to prevent future exposure"

# Generate new secure keys
echo "\n🔑 Generate new secure keys:"
echo "API_KEY=$(openssl rand -hex 32)" > .new-keys-template.txt
echo "NEO4J_PASSWORD=$(openssl rand -hex 16)" >> .new-keys-template.txt
echo "SESSION_SECRET=$(openssl rand -hex 24)" >> .new-keys-template.txt

echo -e "  ${GREEN}✅ New secure keys generated in .new-keys-template.txt${NC}"
echo "     Copy desired keys to .env and delete template file"

echo "\n✅ Security cleanup recommendations complete"
echo "   Review all findings above before deployment"
