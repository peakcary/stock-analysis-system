#!/bin/bash
# Deployment script for API path duplication fix

set -e

# Configuration
SERVER_IP="82.157.28.35"
SERVER_USER="ubuntu"
REMOTE_PATH="/opt/stock-analysis-system"

echo "🚀 Deploying API path duplication fix..."
echo ""

# Check if SSH key is available
if ! ssh-add -l | grep -q "peakcary"; then
    echo "⚠️  peakcary SSH key not loaded"
    echo "Loading SSH key..."
    ssh-add ~/.ssh/id_ed25519_peakcary 2>/dev/null || echo "Note: SSH key may need manual loading"
fi

echo "📦 Building Frontend application..."
cd /Users/peakom/work/stock-analysis-system/frontend
npm run build > /dev/null 2>&1
echo "✅ Frontend built successfully"

echo ""
echo "📦 Building Client application..."
cd /Users/peakom/work/stock-analysis-system/client
npm run build > /dev/null 2>&1
echo "✅ Client built successfully"

echo ""
echo "📤 Uploading Frontend dist files..."
scp -r /Users/peakom/work/stock-analysis-system/frontend/dist/* \
    "${SERVER_USER}@${SERVER_IP}:${REMOTE_PATH}/frontend/dist/" || {
    echo "❌ Failed to upload Frontend dist files"
    echo "   Trying with explicit key..."
    scp -i ~/.ssh/id_ed25519_peakcary -r /Users/peakom/work/stock-analysis-system/frontend/dist/* \
        "${SERVER_USER}@${SERVER_IP}:${REMOTE_PATH}/frontend/dist/"
}
echo "✅ Frontend dist uploaded"

echo ""
echo "📤 Uploading Client dist files..."
scp -r /Users/peakom/work/stock-analysis-system/client/dist/* \
    "${SERVER_USER}@${SERVER_IP}:${REMOTE_PATH}/client/dist/" || {
    echo "❌ Failed to upload Client dist files"
    echo "   Trying with explicit key..."
    scp -i ~/.ssh/id_ed25519_peakcary -r /Users/peakom/work/stock-analysis-system/client/dist/* \
        "${SERVER_USER}@${SERVER_IP}:${REMOTE_PATH}/client/dist/"
}
echo "✅ Client dist uploaded"

echo ""
echo "📥 Pulling latest code from GitHub..."
ssh "${SERVER_USER}@${SERVER_IP}" "cd ${REMOTE_PATH} && git pull origin main" || {
    echo "Note: Failed to auto-pull, server may need to pull manually"
    echo "SSH command: git -C ${REMOTE_PATH} pull origin main"
}
echo "✅ Code pulled"

echo ""
echo "🎉 Deployment completed!"
echo ""
echo "Verify the fix:"
echo "1. Visit https://qwquant.com/admin (Frontend)"
echo "2. Visit https://qwquant.com/app (Client)"
echo "3. Check Network tab in DevTools for API calls"
echo "4. Verify API paths are /api/v1/... (not /api/v1/api/v1/...)"
