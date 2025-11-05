# API Path Duplication Fix - Deployment Guide

## Summary of Changes

The API path duplication issue has been fixed in commit `9a5cfaba`.

**Issue**: API calls were being duplicated, resulting in paths like `/api/v1/api/v1/stocks/count`

**Root Cause**:
- Frontend axios client had baseURL set to `/api/v1`
- All API calls were using absolute paths like `/api/v1/stocks/count`
- This resulted in duplication when combined

**Solution**:
- Changed `getApiBaseUrl()` in `shared/auth-config.ts` to return root origin URL instead of origin + `/api/v1`
- Updated authentication endpoint paths to include `/api/v1` prefix
- All existing API calls with `/api/v1/` prefix now work correctly

## Files Modified

1. **shared/auth-config.ts**
   - Line 51: Changed from `${window.location.origin}/api/v1` to `window.location.origin`
   - Lines 65-68: Updated USER_AUTH_CONFIG endpoints to include `/api/v1` prefix
   - Lines 84-87: Updated ADMIN_AUTH_CONFIG endpoints to include `/api/v1` prefix

## Deployment Steps

### Option 1: Via Git Push (Preferred - Uses Auto-Deployment)
```bash
# The commit has already been pushed to GitHub (9a5cfaba)
# Push to production server:
git push production main

# This will trigger the post-receive hook which will:
# 1. Fetch latest changes from origin main
# 2. Build frontend and client applications
# 3. Deploy the updated applications
```

### Option 2: Manual Deployment (If SSH Access Issues)

**If SSH to server is having issues**, you can manually upload the built dist files:

```bash
# 1. Build the applications locally (already done)
cd frontend && npm run build
cd ../client && npm run build

# 2. Upload to server
# Copy frontend dist
scp -r frontend/dist/* ubuntu@82.157.28.35:/opt/stock-analysis-system/frontend/dist/

# Copy client dist
scp -r client/dist/* ubuntu@82.157.28.35:/opt/stock-analysis-system/client/dist/

# 3. SSH into server and pull the code changes
ssh ubuntu@82.157.28.35
cd /opt/stock-analysis-system
git pull origin main
```

## Verification

After deployment, verify the fix by:

1. **Check API endpoint format** in browser DevTools:
   - Open https://qwquant.com/admin
   - Open Network tab in DevTools
   - Check that API calls are to paths like `/api/v1/stocks/count` (not `/api/v1/api/v1/...`)

2. **Test API functionality**:
   - Login should work correctly
   - Data loading should function properly
   - No 404 errors for API calls

3. **Check specific endpoints**:
   - Stocks endpoint: Should be `/api/v1/stocks`
   - Admin auth: Should be `/api/v1/admin/auth/login`
   - User management: Should be `/api/v1/admin/client-users/users`

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
// If baseURL = "http://example.com/api/v1"
// And you call: apiClient.get('/admin/auth/login')
// Result: http://example.com/api/v1/admin/auth/login

// If baseURL = "http://example.com"
// And you call: apiClient.get('/api/v1/admin/auth/login')
// Result: http://example.com/api/v1/admin/auth/login
```

The fix changed the baseURL handling to use the second pattern, which aligns with all the absolute path API calls throughout the codebase.

### How Nginx Routes API Requests

```
Client Request: GET /api/v1/stocks (via axios with baseURL = root)
              ↓
        Nginx Config
              ↓
        location /api {
            proxy_pass http://backend;
        }
              ↓
Backend receives: GET /stocks (prefix removed by proxy_pass)
```

The nginx configuration properly removes the `/api/v1` prefix when proxying to the backend.

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
