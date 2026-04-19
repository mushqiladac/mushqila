#!/bin/bash
# Fix GitHub Actions SSH Authentication
# Run this script on EC2 server

set -e

echo "=========================================="
echo "🔧 Fixing GitHub Actions SSH Authentication"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Step 1: Checking current SSH configuration...${NC}"
echo ""

# Check SSH directory permissions
echo "📁 SSH directory permissions:"
ls -la ~/.ssh/

echo ""
echo "📄 Authorized keys:"
cat ~/.ssh/authorized_keys

echo ""
echo -e "${YELLOW}Step 2: Fixing SSH directory permissions...${NC}"
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
echo -e "${GREEN}✓ Permissions fixed${NC}"

echo ""
echo -e "${YELLOW}Step 3: Checking SSH daemon configuration...${NC}"
echo ""
echo "Current SSH config:"
sudo grep -E "^(PubkeyAuthentication|AuthorizedKeysFile|PasswordAuthentication)" /etc/ssh/sshd_config || echo "No specific config found"

echo ""
echo -e "${YELLOW}Step 4: Generating new SSH key pair for GitHub Actions...${NC}"
echo ""

# Generate new key pair
SSH_KEY_PATH=~/.ssh/github_actions_key

if [ -f "$SSH_KEY_PATH" ]; then
    echo -e "${YELLOW}⚠️  Key already exists. Creating backup...${NC}"
    mv $SSH_KEY_PATH ${SSH_KEY_PATH}.backup
    mv ${SSH_KEY_PATH}.pub ${SSH_KEY_PATH}.pub.backup
fi

ssh-keygen -t rsa -b 4096 -f $SSH_KEY_PATH -N "" -C "github-actions@mushqila"
echo -e "${GREEN}✓ New key pair generated${NC}"

echo ""
echo -e "${YELLOW}Step 5: Adding public key to authorized_keys...${NC}"
cat ${SSH_KEY_PATH}.pub >> ~/.ssh/authorized_keys
echo -e "${GREEN}✓ Public key added${NC}"

echo ""
echo -e "${YELLOW}Step 6: Testing SSH connection locally...${NC}"
ssh -i $SSH_KEY_PATH -o StrictHostKeyChecking=no ubuntu@localhost "echo 'SSH test successful'" && echo -e "${GREEN}✓ Local SSH test passed${NC}" || echo -e "${RED}✗ Local SSH test failed${NC}"

echo ""
echo "=========================================="
echo -e "${GREEN}✅ SSH Configuration Complete!${NC}"
echo "=========================================="
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo ""
echo "1. Copy the PRIVATE KEY below:"
echo ""
echo "========== PRIVATE KEY START =========="
cat $SSH_KEY_PATH
echo "========== PRIVATE KEY END =========="
echo ""
echo "2. Go to GitHub Repository Settings:"
echo "   https://github.com/mushqiladac/mushqila/settings/secrets/actions"
echo ""
echo "3. Update the secret 'EC2_SSH_KEY' with the private key above"
echo ""
echo "4. Trigger a new deployment from GitHub Actions"
echo ""
echo "=========================================="
echo ""
echo -e "${YELLOW}💡 Tips:${NC}"
echo "- Copy the ENTIRE private key including BEGIN and END lines"
echo "- Don't add extra spaces or newlines"
echo "- The key should start with: -----BEGIN RSA PRIVATE KEY-----"
echo "- The key should end with: -----END RSA PRIVATE KEY-----"
echo ""
echo "=========================================="
