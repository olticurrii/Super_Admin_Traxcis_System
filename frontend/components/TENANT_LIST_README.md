# TenantList Component

## Overview
The `TenantList` component displays all tenant databases in the system with their details including database information, admin email, and creation date.

## Features

### Display Information
- **Tenant Name & ID**: Shows the tenant name and unique identifier
- **Status Badge**: Visual indicator showing if tenant is active or inactive
- **Database Details**: 
  - Database name
  - Database user
  - Database port
- **Server Information**: Database host
- **Admin Email**: Email of the tenant administrator
- **Creation Date**: Timestamp of when the tenant was created

### User Interactions
- **Auto-refresh**: Automatically refreshes when a new tenant is created
- **Manual Refresh**: Button to manually refresh the tenant list
- **Loading States**: Shows loading spinner while fetching data
- **Error Handling**: Displays error messages with retry option
- **Empty State**: Shows helpful message when no tenants exist

### Visual Design
- **Color-coded sections**: Different colors for database, server, and admin info
- **Responsive layout**: Works on all screen sizes (mobile to desktop)
- **Hover effects**: Smooth transitions on interactive elements
- **Status indicators**: Green for active, gray for inactive tenants

## API Integration

### Endpoint Used
- **GET** `/super-admin/tenants`
  - Returns: `Array<TenantInfo>`
  - Parameters: 
    - `skip` (optional): Number of records to skip
    - `limit` (optional): Maximum number of records to return

### Data Structure
```typescript
interface TenantInfo {
  id: number;
  name: string;
  db_name: string;
  db_host: string;
  db_port: string;
  db_user: string;
  admin_email: string;
  status: string;
  created_at: string;
}
```

## Usage

The component is used in the main page (`app/page.tsx`) and automatically refreshes when a new tenant is created:

```tsx
import TenantList from '@/components/TenantList';

// In your component
const [refreshTenantList, setRefreshTenantList] = useState(0);

// Trigger refresh by updating the key
<TenantList key={refreshTenantList} />

// When a tenant is created
setRefreshTenantList(prev => prev + 1);
```

## Security Notes
- **No sensitive data**: Passwords are NOT displayed in the list
- **Read-only view**: The list is for viewing only, no edit/delete capabilities
- Database password is not exposed (only shown in `TenantInfo` schema but excluded from display)

## Dependencies
- `react` - For component functionality
- `lucide-react` - For icons (Database, Mail, Server, Calendar, etc.)
- `date-fns` - For date formatting
- `@/lib/api` - For API calls
- `@/lib/types` - For TypeScript types

## Future Enhancements
Potential improvements that could be added:
- Search/filter functionality
- Sorting by different columns
- Pagination for large tenant lists
- Edit tenant details
- Delete tenant functionality (with confirmation)
- View detailed tenant metrics/statistics
- Export tenant list to CSV

