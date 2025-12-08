# Quick Start & Testing Guide

## Prerequisites

Make sure both backend and frontend are running:

### Terminal 1 - Backend
```bash
cd /Users/olti/Desktop/Projektet\ e\ oltit/Super_Admin_Traxcis_System
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload --port 8001
```

### Terminal 2 - Frontend
```bash
cd /Users/olti/Desktop/Projektet\ e\ oltit/Super_Admin_Traxcis_System/frontend
npm run dev
```

## Testing the New Features

### 1. View Tenant List

**Via Browser:**
1. Open http://localhost:3000
2. Scroll down to see the "Tenant Databases" section
3. You should see all existing tenants listed

**Via API:**
```bash
curl http://localhost:8001/super-admin/tenants
```

### 2. Test Search Functionality

**Via Browser:**
1. Navigate to http://localhost:3000
2. In the tenant list header, find the search box
3. Try searching for:
   - Company name: "acme"
   - Email: "admin@"
   - Database: "tenant_"
   - ID number: "1"
4. Results should filter in real-time
5. Click the X button to clear search

**Expected behavior:**
- Results update instantly as you type
- Counter shows "X of Y tenants (filtered)"
- No results? See "No tenants match your filters" message

### 3. Test Status Filter

**Via Browser:**
1. Navigate to http://localhost:3000
2. Click the "Active" button
3. Only active tenants should display
4. Click "Inactive" button
5. Only inactive tenants should display
6. Click "All" to show everything

**Expected behavior:**
- Selected filter button is white with dark text
- Unselected buttons are semi-transparent white
- Counter updates to show filtered count

### 4. Test Combined Search + Filter

**Via Browser:**
1. Click "Active" filter
2. Type a search query
3. Results should match BOTH criteria
4. Counter shows filtered count

### 5. Test Delete Functionality

⚠️ **Warning:** This will actually delete tenant records!

**Via Browser:**
1. Navigate to http://localhost:3000
2. Find a test tenant you want to delete
3. Click the red trash icon on the tenant card
4. Review the confirmation modal
5. Read the warning about database cleanup
6. Click "Delete Tenant" to confirm
7. Tenant should disappear from the list

**Via API:**
```bash
# Replace 5 with actual tenant ID
curl -X DELETE http://localhost:8001/super-admin/tenants/5
```

**Expected response:**
```json
{
  "message": "Tenant record deleted successfully",
  "tenant_id": 5,
  "db_name": "tenant_test_1702123456",
  "note": "The PostgreSQL database was not automatically deleted. Manual cleanup may be required."
}
```

### 6. Test Delete Confirmation Modal

**Via Browser:**
1. Click delete icon
2. Modal should appear with:
   - Warning icon
   - "Delete Tenant?" title
   - Tenant details (name, database, email)
   - Yellow warning box about database cleanup
   - Cancel and Delete buttons
3. Click "Cancel" - modal closes, no deletion
4. Click outside modal - should stay open (or close, based on implementation)
5. Try again, click "Delete Tenant" - tenant is removed

### 7. Test Delete - Non-existent Tenant

**Via API:**
```bash
curl -X DELETE http://localhost:8001/super-admin/tenants/99999
```

**Expected response (404):**
```json
{
  "detail": "Tenant with ID 99999 not found"
}
```

### 8. Test Empty States

**Test 1: No tenants at all**
1. Delete all tenants (or use fresh database)
2. Visit http://localhost:3000
3. Should see "No Tenants Found" message with icon

**Test 2: No filtered results**
1. Apply a filter that matches nothing
2. Search for text that doesn't exist
3. Should see "No tenants match your filters"
4. Click "Clear Filters" button
5. Should return to full list

### 9. Test Refresh Button

**Via Browser:**
1. Open http://localhost:3000 in two browser tabs
2. In tab 1, delete a tenant
3. In tab 2, click the refresh icon (rotating arrows)
4. The deleted tenant should disappear
5. Watch for spinning animation during refresh

### 10. Test Responsive Design

**Via Browser:**
1. Open http://localhost:3000
2. Resize browser window to mobile size
3. Check that:
   - Search bar stacks vertically
   - Filter buttons wrap or scroll
   - Tenant cards remain readable
   - Delete button stays accessible
   - Modal fits on screen

### 11. Create and Verify Auto-refresh

**Via Browser:**
1. Open http://localhost:3000
2. Create a new tenant using the form
3. After creation, scroll down to tenant list
4. The new tenant should automatically appear
5. No manual refresh needed

## Feature Checklist

Use this checklist to verify all features work:

- [ ] Tenant list displays with all tenants
- [ ] Search box filters by name
- [ ] Search box filters by email
- [ ] Search box filters by database name
- [ ] Search box filters by ID
- [ ] Clear button (X) resets search
- [ ] "All" filter shows all tenants
- [ ] "Active" filter shows only active
- [ ] "Inactive" filter shows only inactive
- [ ] Search + filter work together
- [ ] Counter shows correct filtered count
- [ ] Delete button opens modal
- [ ] Modal shows correct tenant details
- [ ] Modal shows warning about database
- [ ] Cancel button closes modal without deleting
- [ ] Delete button removes tenant from list
- [ ] Deleting shows loading state
- [ ] API returns correct delete response
- [ ] Delete of non-existent tenant returns 404
- [ ] Refresh button updates list
- [ ] Refresh button shows loading animation
- [ ] Auto-refresh after creating tenant
- [ ] Empty state shown when no tenants
- [ ] No results state shown when filtered empty
- [ ] Clear filters button works
- [ ] Responsive design on mobile
- [ ] No console errors

## Common Issues & Solutions

### Backend not starting
```bash
# Error: "Address already in use"
# Solution: Kill the process on port 8001
lsof -ti:8001 | xargs kill -9

# Then restart
uvicorn app.main:app --reload --port 8001
```

### Frontend not starting
```bash
# Error: "Port 3000 is already in use"
# Solution: Use a different port
PORT=3001 npm run dev

# Update NEXT_PUBLIC_API_URL if needed
echo "NEXT_PUBLIC_API_URL=http://localhost:8001" > .env.local
```

### Search not working
- Check browser console for errors
- Verify tenants loaded successfully
- Try hard refresh (Ctrl+Shift+R)

### Delete button not visible
- Check if container is scrollable
- Verify tenant cards loaded
- Check browser zoom level

### Modal not appearing
- Check browser console for errors
- Verify z-index settings
- Check if blocked by popup blocker

### Backend returns 500 error
- Check backend logs in terminal
- Verify database connection
- Check PostgreSQL is running

## Manual Database Cleanup

After deleting tenants, you may want to drop their databases:

```bash
# Connect to PostgreSQL
psql -U postgres

# List all databases
\l

# Find tenant databases (pattern: tenant_*)
\l tenant_*

# Drop a specific tenant database
DROP DATABASE tenant_acme_1702123456;

# Drop all connections first if database is in use
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'tenant_acme_1702123456'
AND pid <> pg_backend_pid();

# Then drop
DROP DATABASE tenant_acme_1702123456;
```

## Performance Testing

### Test with Many Tenants

Create multiple tenants to test performance:

```bash
# Create 20 test tenants
for i in {1..20}; do
  curl -X POST "http://localhost:8001/super-admin/create-tenant" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"Test Company $i\", \"admin_email\": \"admin$i@test.com\"}"
  sleep 2
done
```

Then test:
- Search performance (should be instant)
- Filter performance (should be instant)
- List scrolling (should be smooth)
- Delete performance (should be < 1 second)

## Security Testing

### Test Delete Protection
1. Try to delete without confirmation (not possible via UI)
2. Verify modal requires explicit click
3. Check that database is NOT auto-deleted

### Test API Directly
```bash
# Try to delete with invalid ID
curl -X DELETE http://localhost:8001/super-admin/tenants/abc
# Should return validation error

# Try to delete negative ID
curl -X DELETE http://localhost:8001/super-admin/tenants/-1
# Should return 404
```

## All Tests Passed? ✅

If all tests pass:
- ✅ Search functionality works
- ✅ Filter functionality works
- ✅ Delete functionality works
- ✅ UI is responsive
- ✅ Error handling is proper
- ✅ Performance is good

**Congratulations! The implementation is complete and working!**

## Next Steps

1. **Production Deployment**: Configure environment variables for production
2. **Add Authentication**: Implement login for super admin access
3. **Audit Logging**: Track who deleted which tenants
4. **Backup Strategy**: Backup tenant databases before allowing deletion
5. **Soft Delete**: Consider soft delete instead of hard delete
6. **Bulk Operations**: Add ability to delete multiple tenants at once


