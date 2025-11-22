# Installing Dependencies

## Quick Fix for httpx Error

If you're getting "No module named 'httpx'" error, install the missing dependencies:

### Option 1: Install in Current Environment

```bash
cd "/Users/olti/Desktop/Projektet e oltit/Super_Admin_Traxcis_System"
pip install httpx python-jose email-validator python-dateutil annotated-types typing-extensions
```

### Option 2: Install All Requirements

```bash
cd "/Users/olti/Desktop/Projektet e oltit/Super_Admin_Traxcis_System"
pip install -r requirements.txt
```

### Option 3: If Using Virtual Environment

```bash
cd "/Users/olti/Desktop/Projektet e oltit/Super_Admin_Traxcis_System"

# Create virtual environment if it doesn't exist
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Make sure to run the backend server with the virtual environment activated
uvicorn app.main:app --reload --port 8001
```

## Important Notes

1. **Restart the backend server** after installing dependencies
2. Make sure you're running the server in the **same Python environment** where you installed the packages
3. If using a virtual environment, **activate it before starting the server**

## Verify Installation

Test if httpx is available:
```bash
python3 -c "import httpx; print('httpx installed successfully')"
```

If this works but the server still fails, the server is running in a different Python environment.

