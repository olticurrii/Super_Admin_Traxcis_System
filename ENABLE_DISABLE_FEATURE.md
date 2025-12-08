# Enable/Disable Tenant Feature - Documentation

## 🎯 Overview

The **Enable/Disable** feature allows you to temporarily deactivate tenants without deleting any data. This is a **soft disable** that prevents users from logging into a tenant while keeping all data and the database intact.

## ✨ Key Benefits

- ✅ **Safe**: No data is deleted
- ✅ **Reversible**: Can be easily enabled again
- ✅ **Instant**: Takes effect immediately
- ✅ **Visual**: Clear indicators show disabled tenants
- ✅ **No Database Changes**: Database remains untouched

## 🆚 Disable vs Delete

| Feature | Disable | Delete |
|---------|---------|--------|
| **Data** | Preserved | Record removed |
| **Database** | Untouched | Remains (manual cleanup needed) |
| **Reversible** | ✅ Yes, instantly | ❌ No |
| **User Login** | ❌ Blocked | ❌ Blocked |
| **Best For** | Temporary suspension | Permanent removal |

## 🎨 UI Features

### Status Badge
- **Active**: Green badge with ✓ icon
- **Disabled**: Red badge with ✕ icon and "Disabled" text

### Toggle Button
- **Active Tenant**: Orange power-off icon (disable)
- **Disabled Tenant**: Green power-on icon (enable)
- **Loading**: Spinning animation during toggle

### Visual Indicators
- **Disabled tenants** have:
  - Gray background (opacity 75%)
  - Grayed-out tenant name
  - Red "Disabled" badge
  - Green power button to re-enable

## 📡 API Endpoints

### Toggle Status (Recommended)
```
PATCH /super-admin/tenants/{tenant_id}/toggle-status
```

**Purpose**: Toggles between active ↔ inactive

**Response**:
```json
{
  "id": 5,
  "name": "Acme Corporation",
  "db_name": "tenant_acme_1702123456",
  "status": "inactive",
  "admin_email": "admin@acme.com",
  "db_host": "localhost",
  "db_port": "5432",
  "db_user": "postgres",
  "created_at": "2025-12-07T10:30:00"
}
```

### Set Specific Status
```
PATCH /super-admin/tenants/{tenant_id}/status?status_value=inactive
```

**Purpose**: Set to specific status (active or inactive)

**Parameters**:
- `status_value`: "active" or "inactive"

## 🚀 How to Use

### Via UI (Recommended)

1. Navigate to `http://localhost:3000`
2. Find the tenant you want to disable
3. Click the **power button** icon:
   - Orange power-off icon = Currently active (click to disable)
   - Green power-on icon = Currently disabled (click to enable)
4. Status changes immediately
5. Tenant visual appearance updates

### Via API

**Disable a tenant:**
```bash
curl -X PATCH http://localhost:8001/super-admin/tenants/5/toggle-status
```

**Enable it again:**
```bash
curl -X PATCH http://localhost:8001/super-admin/tenants/5/toggle-status
```

**Set specific status:**
```bash
# Disable
curl -X PATCH "http://localhost:8001/super-admin/tenants/5/status?status_value=inactive"

# Enable
curl -X PATCH "http://localhost:8001/super-admin/tenants/5/status?status_value=active"
```

## 🔒 What Happens When Disabled

### ✅ What's Preserved
- All tenant data remains intact
- Database is untouched
- All tables and records preserved
- Tenant metadata remains in super_admin_db
- Database credentials still valid

### ❌ What's Blocked
- Users **cannot login** to the tenant (you need to implement this in your HRMS login logic)
- Tenant appears as "Disabled" in admin panel
- Visual indicators show inactive state

## 🏗️ Implementation in HRMS Login

To actually block logins for disabled tenants, you need to check the status in your HRMS login endpoint:

```python
# In your HRMS login endpoint
from app.superadmin.service import get_tenant_by_db_name

async def login(email: str, password: str, db: Session):
    # Get tenant info from super_admin_db
    tenant = get_tenant_by_db_name(super_admin_db, current_db_name)
    
    # Check if tenant is active
    if not tenant or tenant.status != "active":
        raise HTTPException(
            status_code=403,
            detail="This tenant is currently disabled. Please contact support."
        )
    
    # Continue with normal login logic
    # ...
```

## 🎯 Use Cases

### Temporary Suspension
```
Scenario: Client hasn't paid their bill
Action: Disable tenant
Result: Users can't login, but data is safe
Later: Payment received → Enable tenant → Users can login again
```

### Maintenance Mode
```
Scenario: Need to perform maintenance on tenant data
Action: Disable tenant
Result: Users can't access while you work
Later: Maintenance done → Enable tenant
```

### Testing
```
Scenario: Testing new features
Action: Disable production tenant, test on copy
Result: Users unaffected
Later: Testing done → Re-enable
```

### Migration
```
Scenario: Migrating to new infrastructure
Action: Disable old tenant
Result: Prevent data changes during migration
Later: Migration complete → Enable on new system
```

## 📊 Status Values

| Status | Description | User Login | Visual |
|--------|-------------|------------|--------|
| `active` | Normal operation | ✅ Allowed | Green badge |
| `inactive` | Disabled/suspended | ❌ Blocked | Red badge, grayed out |

## 🔧 Technical Details

### Backend Service Function
```python
def toggle_tenant_status(db: Session, tenant_id: int) -> Tenant:
    """Toggle between active and inactive"""
    tenant = get_tenant_by_id(db, tenant_id)
    tenant.status = "inactive" if tenant.status == "active" else "active"
    db.commit()
    return tenant
```

### Frontend API Call
```typescript
export const toggleTenantStatus = async (tenantId: number): Promise<TenantInfo> => {
  const response = await apiClient.patch(`/super-admin/tenants/${tenantId}/toggle-status`);
  return response.data;
};
```

### Component State Management
```typescript
const [togglingStatus, setTogglingStatus] = useState<number | null>(null);

const handleToggleStatus = async (tenant: TenantInfo) => {
  setTogglingStatus(tenant.id);
  const updatedTenant = await toggleTenantStatus(tenant.id);
  setTenants(tenants.map(t => t.id === tenant.id ? updatedTenant : t));
  setTogglingStatus(null);
};
```

## 🎨 Visual States

### Active Tenant Card
```
┌─────────────────────────────────────────────────┐
│ Acme Corporation  [✓ Active]          ⏻ 🗑️    │
│ ID: 5                                           │
│ [Database Info]  [Server & Admin Info]         │
└─────────────────────────────────────────────────┘
```

### Disabled Tenant Card
```
┌─────────────────────────────────────────────────┐
│ Acme Corporation  [✕ Disabled]        ⏻ 🗑️    │  ← Grayed out
│ ID: 5                                           │  ← Background gray
│ [Database Info]  [Server & Admin Info]         │
└─────────────────────────────────────────────────┘
```

### During Toggle (Loading)
```
┌─────────────────────────────────────────────────┐
│ Acme Corporation  [✓ Active]          ⟳ 🗑️    │  ← Spinner
│ ID: 5                                           │
└─────────────────────────────────────────────────┘
```

## 🧪 Testing

### Test Disable
1. Start with an active tenant
2. Click the orange power-off button
3. Badge changes from green "Active" to red "Disabled"
4. Card gets gray background
5. Button changes to green power-on icon
6. Status updates in database

### Test Enable
1. Start with a disabled tenant
2. Click the green power-on button
3. Badge changes from red "Disabled" to green "Active"
4. Card background returns to normal
5. Button changes to orange power-off icon
6. Status updates in database

### Test Filter
1. Disable a few tenants
2. Click "Inactive" filter button
3. Only disabled tenants show
4. Click "Active" filter
5. Only active tenants show

### Test API
```bash
# Test toggle endpoint
curl -X PATCH http://localhost:8001/super-admin/tenants/5/toggle-status

# Check response
# Should show status: "inactive" or "active"

# Toggle again
curl -X PATCH http://localhost:8001/super-admin/tenants/5/toggle-status

# Status should flip back
```

## ⚠️ Important Notes

1. **Database Not Affected**: Disabling does NOT touch the database
2. **Instant Effect**: Status changes immediately in UI
3. **Reversible**: Can be toggled back and forth unlimited times
4. **Login Check Required**: You must implement login blocking in HRMS
5. **No Data Loss**: 100% safe operation

## 🔄 Workflow Comparison

### Old Workflow (Delete Only)
```
Problem with tenant → Delete record → Database still exists → Manual cleanup → Data lost
                                                              ↓
                                                         Can't undo
```

### New Workflow (Disable)
```
Problem with tenant → Disable → Users can't login → Problem solved → Enable again
                                       ↓                                  ↓
                                 Data safe                          Back to normal
```

## 📋 Quick Reference

| Action | Button | Icon | Color | Result |
|--------|--------|------|-------|--------|
| Disable | Power-off | ⏻ (off) | Orange | Set to inactive |
| Enable | Power-on | ⏻ (on) | Green | Set to active |
| Delete | Trash | 🗑️ | Red | Remove record |

## 🎉 Summary

The enable/disable feature provides a **safe, reversible way** to temporarily suspend tenants without:
- ❌ Deleting any data
- ❌ Dropping databases
- ❌ Losing tenant information
- ❌ Permanent changes

Perfect for:
- ✅ Payment issues
- ✅ Maintenance windows
- ✅ Contract suspensions
- ✅ Testing scenarios
- ✅ Temporary deactivation

**Much safer than deletion!** 🛡️

