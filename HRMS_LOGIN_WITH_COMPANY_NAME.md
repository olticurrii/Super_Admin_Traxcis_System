# 🔐 HRMS Login with Company Name - Implementation Guide

## 🎯 The Solution

Instead of looking up tenants by email (which only works for admins), users now login with:
- **Company Name** (e.g., "Traxcis")
- **Email**
- **Password**

This allows **ANY user** in the company to login without pre-registration!

---

## 🚀 New API Endpoint

### Primary Endpoint: `GET /tenants/find-by-company/{company_name}`

**This is the NEW endpoint for HRMS login!**

**Request:**
```http
GET /tenants/find-by-company/Traxcis
```

**Response (200 OK):**
```json
{
  "tenant_id": 5,
  "db_url": "postgresql+psycopg2://user:pass@host:5432/tenant_traxcis_123",
  "company_name": "Traxcis"
}
```

**Response (404 Not Found):**
```json
{
  "detail": "No active tenant found for company: InvalidCompany"
}
```

**Features:**
- ✅ Case-insensitive search (`Traxcis` = `traxcis` = `TRAXCIS`)
- ✅ Only returns active tenants
- ✅ Works for ALL users (no pre-registration needed)
- ✅ Fast indexed lookup

---

## 📋 Updated Login Flow

### Step 1: User Enters Credentials

```
┌─────────────────────────────────┐
│  Login to HRMS                  │
├─────────────────────────────────┤
│                                 │
│  Company:  [Traxcis          ]  │ ← NEW FIELD!
│  Email:    [john@traxcis.com ]  │
│  Password: [****************]  │
│                                 │
│         [Login Button]          │
└─────────────────────────────────┘
```

### Step 2: HRMS Backend Flow

```javascript
// 1. Get company name from login form
const { companyName, email, password } = loginData;

// 2. Find tenant by company name
const tenantResponse = await fetch(
  `https://super-admin-traxcis-system.onrender.com/tenants/find-by-company/${encodeURIComponent(companyName)}`
);

if (!tenantResponse.ok) {
  throw new Error("Company not found");
}

const { tenant_id, db_url, company_name } = await tenantResponse.json();

// 3. Connect to tenant's database using db_url
// 4. Validate email + password in tenant database
// 5. Return JWT token if valid
```

---

## 💻 Frontend Implementation

### React/Next.js Example

```typescript
// LoginForm.tsx
import { useState } from 'react';

interface LoginFormData {
  companyName: string;
  email: string;
  password: string;
}

export default function LoginForm() {
  const [formData, setFormData] = useState<LoginFormData>({
    companyName: '',
    email: '',
    password: ''
  });
  const [error, setError] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Step 1: Find tenant by company name
      const tenantResponse = await fetch(
        `https://super-admin-traxcis-system.onrender.com/tenants/find-by-company/${encodeURIComponent(formData.companyName)}`
      );

      if (!tenantResponse.ok) {
        throw new Error('Company not found. Please check the company name.');
      }

      const { tenant_id, db_url } = await tenantResponse.json();

      // Step 2: Login with tenant database
      const loginResponse = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password,
          tenant_id,
          db_url
        })
      });

      if (!loginResponse.ok) {
        throw new Error('Invalid email or password');
      }

      const { token } = await loginResponse.json();
      
      // Store token and redirect
      localStorage.setItem('token', token);
      window.location.href = '/dashboard';

    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="companyName" className="block text-sm font-medium">
          Company Name
        </label>
        <input
          id="companyName"
          type="text"
          required
          value={formData.companyName}
          onChange={(e) => setFormData({ ...formData, companyName: e.target.value })}
          placeholder="e.g., Traxcis"
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
        />
        <p className="mt-1 text-xs text-gray-500">
          Enter your company name as provided by your admin
        </p>
      </div>

      <div>
        <label htmlFor="email" className="block text-sm font-medium">
          Email
        </label>
        <input
          id="email"
          type="email"
          required
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          placeholder="john@company.com"
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
        />
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium">
          Password
        </label>
        <input
          id="password"
          type="password"
          required
          value={formData.password}
          onChange={(e) => setFormData({ ...formData, password: e.target.value })}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
        />
      </div>

      {error && (
        <div className="text-red-600 text-sm">{error}</div>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700"
      >
        {loading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
}
```

---

## 🔧 Backend Implementation

### FastAPI/Python Example

```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
import requests

router = APIRouter()

class LoginRequest(BaseModel):
    company_name: str
    email: str
    password: str

class LoginResponse(BaseModel):
    token: str
    user: dict

@router.post("/auth/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """Login endpoint that uses company name to find tenant."""
    
    # Step 1: Find tenant by company name
    super_admin_url = "https://super-admin-traxcis-system.onrender.com"
    tenant_response = requests.get(
        f"{super_admin_url}/tenants/find-by-company/{credentials.company_name}"
    )
    
    if tenant_response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="Company not found. Please check the company name."
        )
    
    if tenant_response.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail="Failed to lookup company"
        )
    
    tenant_data = tenant_response.json()
    db_url = tenant_data["db_url"]
    tenant_id = tenant_data["tenant_id"]
    
    # Step 2: Connect to tenant's database
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Step 3: Find user by email in tenant database
        from app.models import User  # Your HRMS User model
        
        user = db.query(User).filter(User.email == credentials.email).first()
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        # Step 4: Verify password
        from app.security import verify_password
        
        if not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        # Step 5: Generate JWT token
        from app.security import create_access_token
        
        token = create_access_token({
            "user_id": user.id,
            "email": user.email,
            "tenant_id": tenant_id
        })
        
        return LoginResponse(
            token=token,
            user={
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "tenant_id": tenant_id
            }
        )
        
    finally:
        db.close()
```

---

## 📊 Complete Flow Diagram

```
┌─────────────┐
│   User      │
│  Enters:    │
│  - Company  │  
│  - Email    │
│  - Password │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  HRMS Frontend                          │
│  POST /api/auth/login                   │
│  {                                      │
│    company_name: "Traxcis",            │
│    email: "john@traxcis.com",          │
│    password: "secret"                   │
│  }                                      │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  HRMS Backend                           │
│  Step 1: Find Tenant                    │
│  GET /tenants/find-by-company/Traxcis   │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  Super Admin Service                    │
│  Returns:                               │
│  {                                      │
│    tenant_id: 5,                       │
│    db_url: "postgresql://...",         │
│    company_name: "Traxcis"             │
│  }                                      │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  HRMS Backend                           │
│  Step 2: Connect to Tenant DB           │
│  using db_url                           │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  Tenant Database                        │
│  Step 3: Verify email + password        │
│  SELECT * FROM users                    │
│  WHERE email = 'john@traxcis.com'      │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  HRMS Backend                           │
│  Step 4: Generate JWT Token             │
│  Return: { token, user }                │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  HRMS Frontend                          │
│  Step 5: Store token                    │
│  Redirect to /dashboard                 │
└─────────────────────────────────────────┘
```

---

## ✅ Benefits of Company-Based Login

1. **✅ No Pre-Registration Required**
   - ANY user in the company can login
   - No need to register users with Super Admin first

2. **✅ Better User Experience**
   - Users enter their company name (easy to remember)
   - More intuitive than email-only lookup

3. **✅ Works for All Users**
   - Admins and regular employees use the same flow
   - No special handling needed

4. **✅ Fast and Reliable**
   - Indexed database lookup
   - Case-insensitive search
   - Only returns active tenants

---

## 🔒 Security Considerations

1. **Rate Limiting**: Consider adding rate limiting to prevent brute force attacks
2. **Invalid Company Names**: Return generic error messages to avoid leaking info
3. **Password Validation**: Still happens in tenant database (secure)
4. **Active Tenants Only**: Inactive tenants cannot be accessed

---

## 🧪 Testing

### Test Case 1: Valid Login
```bash
# Step 1: Find tenant
curl https://super-admin-traxcis-system.onrender.com/tenants/find-by-company/Traxcis

# Expected: 200 OK with tenant info
```

### Test Case 2: Invalid Company
```bash
curl https://super-admin-traxcis-system.onrender.com/tenants/find-by-company/InvalidCompany

# Expected: 404 Not Found
```

### Test Case 3: Case Insensitive
```bash
# All should work:
/tenants/find-by-company/Traxcis
/tenants/find-by-company/traxcis
/tenants/find-by-company/TRAXCIS
```

---

## 📝 Migration Checklist

- [ ] Update HRMS login form to include "Company Name" field
- [ ] Update HRMS backend to call `/tenants/find-by-company/{company_name}`
- [ ] Test login with different company names
- [ ] Test case-insensitive company names
- [ ] Test with both admin and regular user accounts
- [ ] Update user documentation with new login flow
- [ ] Remove old email-based lookup code (optional, kept for backwards compat)

---

## 🆘 Troubleshooting

### Error: "Company not found"
- **Cause**: Company name doesn't match any tenant
- **Solution**: Check company name spelling, check Super Admin dashboard for correct name

### Error: "Invalid email or password"
- **Cause**: User doesn't exist in tenant database OR wrong password
- **Solution**: Verify user exists in HRMS, check password is correct

### Error: "No active tenant found"
- **Cause**: Tenant is inactive/disabled
- **Solution**: Contact admin to enable tenant in Super Admin dashboard

---

## ✅ Summary

**New Login Flow:**
1. User enters: Company Name + Email + Password
2. HRMS calls: `GET /tenants/find-by-company/{company_name}`
3. Get tenant's `db_url`
4. Connect to tenant database
5. Verify email + password
6. Return JWT token
7. User logged in! 🎉

**Key Endpoint:**
```
GET /tenants/find-by-company/{company_name}
```

**Works for ALL users - no registration needed!** 🚀

