# Troubleshooting Guide

## 404 Error: Backend Not Found

If you're seeing a 404 error, it usually means the FastAPI backend is not running or not accessible.

### Quick Fixes

1. **Check if backend is running:**
   ```bash
   # In the root directory (Super_Admin_Traxcis_System)
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Verify the API URL:**
   - Check that `.env.local` exists in the `frontend/` directory
   - It should contain: `NEXT_PUBLIC_API_URL=http://localhost:8001`
   - If the file doesn't exist, create it:
     ```bash
     cd frontend
     echo "NEXT_PUBLIC_API_URL=http://localhost:8001" > .env.local
     ```

3. **Restart the frontend after creating .env.local:**
   ```bash
   # Stop the dev server (Ctrl+C) and restart
   npm run dev
   ```

4. **Check backend is accessible:**
   - Open http://localhost:8000/docs in your browser
   - You should see the FastAPI Swagger documentation
   - If not, the backend is not running

### Common Issues

**Issue:** Backend status shows "Offline" in the header
- **Solution:** Start the FastAPI backend server

**Issue:** CORS errors in browser console
- **Solution:** The backend already has CORS enabled. If you still see errors, check that the backend is running on port 8000

**Issue:** Network error or connection refused
- **Solution:** 
  1. Ensure PostgreSQL is running
  2. Ensure the backend server is running
  3. Check firewall settings

### Testing the Backend

Test the backend directly:
```bash
curl http://localhost:8001/health
```

Should return:
```json
{"status":"healthy"}
```

### Testing the Create Tenant Endpoint

```bash
curl -X POST "http://localhost:8001/super-admin/create-tenant" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Company", "admin_email": "admin@test.com"}'
```

