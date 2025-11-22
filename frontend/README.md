# Super Admin Service - Frontend

A modern Next.js admin dashboard for managing tenant databases in the Super Admin Service.

## Features

- 🎨 **Modern UI** - Beautiful, responsive design with Tailwind CSS
- 📱 **Mobile Friendly** - Works seamlessly on all devices
- 🔐 **Secure Password Display** - Shows initial password once with hide/show functionality
- 📋 **Copy to Clipboard** - Easy copying of credentials
- ⚡ **Real-time Feedback** - Instant success/error messages
- 🎯 **Type Safe** - Full TypeScript support

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- The Super Admin Service backend running on `http://localhost:8000`

### Installation

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.local.example .env.local
   ```
   
   Edit `.env.local` and set the API URL if different from default:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8001
   ```

4. **Run the development server:**
   ```bash
   npm run dev
   # or
   yarn dev
   ```

5. **Open your browser:**
   Navigate to [http://localhost:3000](http://localhost:3000)

## Building for Production

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx      # Root layout
│   ├── page.tsx         # Main dashboard page
│   └── globals.css      # Global styles
├── components/
│   ├── TenantForm.tsx   # Create tenant form
│   └── TenantCard.tsx   # Display created tenant credentials
├── lib/
│   ├── api.ts          # API client functions
│   └── types.ts        # TypeScript type definitions
└── public/             # Static assets
```

## Usage

1. **Create a Tenant:**
   - Fill in the tenant name and admin email
   - Click "Create Tenant"
   - The system will:
     - Create a new PostgreSQL database
     - Run HRMS migrations
     - Seed an admin user
     - Generate a secure password

2. **View Credentials:**
   - After creation, credentials appear in the right panel
   - Copy buttons for easy credential copying
   - Password can be hidden/shown for security

3. **Important:**
   - The initial password is shown **only once**
   - Make sure to save it securely
   - You can hide/show it using the toggle button

## Technologies

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client
- **Lucide React** - Icon library
- **date-fns** - Date formatting

## API Integration

The frontend communicates with the FastAPI backend at the URL specified in `NEXT_PUBLIC_API_URL`.

### Endpoints Used

- `POST /super-admin/create-tenant` - Create a new tenant
- `GET /health` - Health check (for future use)

## Customization

### Colors

Edit `tailwind.config.js` to customize the color scheme. The primary color is set to blue (`primary-600`).

### API URL

Change the backend URL by updating `NEXT_PUBLIC_API_URL` in `.env.local`.

## Troubleshooting

### CORS Issues

If you encounter CORS errors, make sure the FastAPI backend has CORS middleware enabled:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Connection Errors

- Verify the backend is running on the correct port
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Ensure both services are on the same network

## License

This is a proprietary frontend for the Super Admin Service.

