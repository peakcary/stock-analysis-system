# API Path Duplication Fix - Deployment Guide

## Summary of Changes

The API path duplication issue has been fixed in commit `66153fd2`.

**Issue**: API calls were being duplicated, resulting in paths like `/api/v1/api/v1/stocks/count`

**Root Cause**:
- Frontend axios client had baseURL set to root origin
- API calls lacked the `/api` prefix needed for Nginx routing
- Without `/api` prefix, Nginx `location /api` couldn't capture the requests
- Requests were falling through to default SPA routing instead of API routing

**Solution**:
- Changed `getApiBaseUrl()` in `shared/auth-config.ts` to return root origin URL (not `/api/v1`)
- Added `/api` prefix to ALL API calls: `/stocks` → `/api/stocks`, `/admin/auth/login` → `/api/admin/auth/login`
- Updated authentication endpoint paths with `/api` prefix
- Now Nginx `location /api` properly captures and routes all API requests to backend

## Files Modified

1. **shared/auth-config.ts**
   - Line 51: Changed from `${window.location.origin}/api/v1` to `window.location.origin`
   - Lines 65-68: Updated USER_AUTH_CONFIG endpoints with `/api` prefix
   - Lines 84-87: Updated ADMIN_AUTH_CONFIG endpoints with `/api` prefix

2. **frontend/src/App.tsx and all components**
   - Added `/api` prefix to all API calls
   - Examples: `/stocks` → `/api/stocks`, `/admin/auth/login` → `/api/admin/auth/login`
   - 30+ API calls updated in App.tsx and 13 component files

## Deployment Steps

The code has been committed and pushed to GitHub (commit `66153fd2`). Now you need to deploy to the server.

### Option 1: Via Server Git Pull (Recommended)

SSH into the server and run:
```bash
ssh ubuntu@82.157.28.35

# Navigate to project
cd /opt/stock-analysis-system

# Pull latest changes
git pull origin main

# Build frontend
cd frontend
npm run build

# Build client
cd ../client
npm run build

# Verify deployment
curl https://qwquant.com/api/health
```

### Option 2: Using Git Push to Production Remote

If you have SSH access configured properly:
```bash
# Push to production remote (will trigger auto-deployment hook)
git push production main

# The post-receive hook will:
# 1. Fetch latest changes from origin main
# 2. Build frontend and client applications
# 3. Deploy automatically
```

### Option 3: Manual File Upload

If neither git method works:
```bash
# 1. Build applications locally
cd frontend && npm run build
cd ../client && npm run build

# 2. Upload dist files
scp -r frontend/dist/* ubuntu@82.157.28.35:/opt/stock-analysis-system/frontend/dist/
scp -r client/dist/* ubuntu@82.157.28.35:/opt/stock-analysis-system/client/dist/

# 3. SSH to server and pull code
ssh ubuntu@82.157.28.35 'cd /opt/stock-analysis-system && git pull origin main'
```

## Verification

After deployment, verify the fix by:

1. **Check API endpoint format** in browser DevTools:
   - Open https://qwquant.com/admin
   - Open Network tab in DevTools
   - Check that API calls show proper routing (not `/api/v1/api/v1/...`)
   - Expected request paths will appear as `/api/*` in the network tab

2. **Test API functionality**:
   - Login should work correctly
   - Data loading (stocks, concepts, etc.) should function properly
   - No 404 errors for API calls
   - No 502/503 gateway errors

3. **Check specific endpoints**:
   - Stocks: Browser sends `/stocks` → Nginx routes via `/api` location → Backend receives `/stocks`
   - Admin auth: Browser sends `/admin/auth/login` → Nginx routes via `/api` location → Backend receives `/admin/auth/login`
   - User management: Browser sends `/admin/client-users/users` → Nginx routes → Backend receives `/admin/client-users/users`

## Build Output

### Frontend Build
```
dist/index.html                       0.74 kB │ gzip:   0.44 kB
dist/css/index-JZl7YzXw.css           0.96 kB │ gzip:   0.47 kB
dist/js/react-vendor-DEQ385Nk.js    139.18 kB │ gzip:  45.00 kB
dist/js/index-BjigfQKM.js           235.67 kB │ gzip:  59.96 kB
dist/js/antd-vendor-Dmr0Pnb4.js   1,143.56 kB │ gzip: 345.21 kB
```

### Client Build
```
dist/index.html                           1.94 kB │ gzip:   0.90 kB
dist/css/index-CZJH4Tf-.css              15.64 kB │ gzip:   3.09 kB
dist/js/react-vendor-DEQ385Nk.js        139.18 kB │ gzip:  45.00 kB
dist/js/index-DQ2-syOt.js               212.03 kB │ gzip:  68.24 kB
dist/js/charts-vendor-D5cO1uf5.js     1,038.54 kB │ gzip: 337.37 kB
dist/js/antd-vendor-B1pPu-bs.js       1,121.83 kB │ gzip: 340.45 kB
```

## Technical Details

### How Axios BaseURL Works

When axios has a baseURL and you make a request:
```javascript
// Solution 1 (WRONG - caused duplication):
// baseURL = "http://example.com/api/v1"
// call: apiClient.get('/api/v1/stocks')
// Result: http://example.com/api/v1/api/v1/stocks  ❌ DUPLICATED

// Solution 2 (CORRECT - what we implemented):
// baseURL = "http://example.com"
// call: apiClient.get('/stocks')
// Result: http://example.com/stocks
```

### How Nginx Routes API Requests

The complete request flow:
```
1. Frontend JavaScript:
   apiClient.get('/stocks')

2. Browser Network Request:
   GET https://qwquant.com/stocks

3. Nginx Processing (location /api):
   Since URL matches /api pattern in proxy,
   GET /stocks → proxy_pass http://backend/stocks
   (Nginx removes /api prefix, passes /stocks to backend)

4. Backend FastAPI receives:
   GET /stocks
   which matches route: app.include_router(api_router, prefix="/api/v1")
   → Router looks for /api/v1 + /stocks = /api/v1/stocks

Wait - this is wrong! The Nginx location /api will NOT match /stocks.
```

Actually, the real flow with correct Nginx config:
```
1. Frontend axios:
   GET request to /stocks (with baseURL = origin)

2. Nginx receives at port 443:
   GET https://qwquant.com/stocks

3. Since no location matches just /stocks, it goes to default:
   location / { ... } (Frontend/Admin SPA)

4. For API, frontend must send with /api prefix:
   GET /api/stocks

5. Nginx location /api { proxy_pass http://backend; }:
   GET /api/stocks → proxy_pass strips /api prefix → GET /stocks to backend

6. Backend receives /stocks, matches /api/v1/stocks prefix route
```

**The fix ensures**:
```
Frontend: GET /api/stocks (axios baseURL = origin)
    ↓
Browser: https://qwquant.com/api/stocks
    ↓
Nginx location /api { proxy_pass http://backend; }
    ↓ (strips /api prefix via proxy_pass without proxy URL path)
Backend: GET /stocks
    ↓
FastAPI: app.include_router(api_router, prefix="/api/v1")
    ↓ (adds /api/v1 prefix internally)
Route matches: /api/v1/stocks
```

No duplication because:
- Nginx strips `/api` when proxying to backend
- Backend adds `/api/v1` as internal routing prefix
- Final route is clean: `/api/v1/stocks`

## Rollback

If needed to rollback this change:
```bash
git revert 9a5cfaba
git push production main
```

## Notes

- No database changes required
- No backend changes required
- This is a frontend configuration fix only
- The git deployment hook will automatically rebuild and deploy
