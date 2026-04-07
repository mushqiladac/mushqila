#!/bin/bash

# Quick script to test SSH and guide through fixing GitHub Actions

echo "=========================================="
echo "🔧 SSH Authentication Fix Helper"
echo "=========================================="
echo ""

# Check if key file is provided
if [ -z "$1" ]; then
    echo "Usage: ./fix-ssh-and-deploy.sh your-key.pem"
    echo ""
    echo "Example:"
    echo "  ./fix-ssh-and-deploy.sh mushqila-key.pem"
    exit 1
fi

KEY_FILE="$1"
EC2_HOST="16.170.25.9"
EC2_USER="ubuntu"

# Check if key file exists
if [ ! -f "$KEY_FILE" ]; then
    echo "❌ Error: Key file '$KEY_FILE' not found"
    exit 1
fi

echo "1. Checking key file format..."
echo ""

# Check key format
FIRST_LINE=$(head -1 "$KEY_FILE")
LAST_LINE=$(tail -1 "$KEY_FILE")

if [[ "$FIRST_LINE" == "-----BEGIN RSA PRIVATE KEY-----" ]]; then
    echo "✅ Key starts correctly: $FIRST_LINE"
else
    echo "❌ Key format issue!"
    echo "   Expected: -----BEGIN RSA PRIVATE KEY-----"
    echo "   Got: $FIRST_LINE"
    echo ""
    echo "   Your key might be in OpenSSH format."
    echo "   Convert it with:"
    echo "   ssh-keygen -p -m PEM -f $KEY_FILE"
    exit 1
fi

if [[ "$LAST_LINE" == "-----END RSA PRIVATE KEY-----" ]]; then
    echo "✅ Key ends correctly: $LAST_LINE"
else
    echo "❌ Key format issue!"
    echo "   Expected: -----END RSA PRIVATE KEY-----"
    echo "   Got: $LAST_LINE"
    exit 1
fi

echo ""
echo "2. Checking key permissions..."
echo ""

# Check permissions (Linux/Mac only)
if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "win32" ]]; then
    PERMS=$(stat -c %a "$KEY_FILE" 2>/dev/null || stat -f %A "$KEY_FILE" 2>/dev/null)
    if [ "$PERMS" != "400" ] && [ "$PERMS" != "600" ]; then
        echo "⚠️  Key permissions: $PERMS (should be 400 or 600)"
        echo "   Fixing permissions..."
        chmod 400 "$KEY_FILE"
        echo "✅ Permissions fixed"
    else
        echo "✅ Key permissions correct: $PERMS"
    fi
fi

echo ""
echo "3. Testing SSH connection..."
echo ""

# Test SSH connection
if ssh -i "$KEY_FILE" -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" "echo 'SSH connection successful!'" 2>/dev/null; then
    echo "✅ SSH connection works!"
    echo ""
    echo "=========================================="
    echo "✅ Your SSH key is working correctly!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Copy your ENTIRE key to clipboard:"
    echo "   cat $KEY_FILE | pbcopy  # Mac"
    echo "   cat $KEY_FILE | xclip -selection clipboard  # Linux"
    echo "   Get-Content $KEY_FILE | Set-Clipboard  # Windows PowerShell"
    echo ""
    echo "2. Go to GitHub Secrets:"
    echo "   https://github.com/mushqiladac/mushqila/settings/secrets/actions"
    echo ""
    echo "3. Update EC2_SSH_KEY:"
    echo "   - Click 'Update' on EC2_SSH_KEY"
    echo "   - Paste the ENTIRE key (including BEGIN and END lines)"
    echo "   - Click 'Update secret'"
    echo ""
    echo "4. Retry deployment:"
    echo "   https://github.com/mushqiladac/mushqila/actions"
    echo "   Click 'Re-run jobs'"
    echo ""
else
    echo "❌ SSH connection failed!"
    echo ""
    echo "Troubleshooting:"
    echo ""
    echo "1. Check EC2 Security Group:"
    echo "   - Go to AWS Console → EC2 → Security Groups"
    echo "   - Ensure port 22 is open for your IP"
    echo ""
    echo "2. Try verbose SSH to see error:"
    echo "   ssh -vvv -i $KEY_FILE $EC2_USER@$EC2_HOST"
    echo ""
    echo "3. Check if EC2 is running:"
    echo "   - AWS Console → EC2 → Instances"
    echo "   - Instance should be 'running'"
    echo ""
    echo "4. Alternative: Use AWS SSM (no SSH needed)"
    echo "   - See: FIX-SSH-AUTHENTICATION.md (Solution 4)"
    echo ""
fi

echo "=========================================="
echo ""
echo "For more help, see: FIX-SSH-AUTHENTICATION.md"
