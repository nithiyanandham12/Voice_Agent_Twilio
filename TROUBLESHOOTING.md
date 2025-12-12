# Troubleshooting Guide

## Port Forwarding Issues

### Cursor/VS Code Port Forwarding Error

If you see an error like:
```
Unable to forward localhost:8000. spawn c:\Program Files\cursor\bin\code-tunnel.exe ENOENT
```

**Solutions:**

1. **Ignore the port forwarding** (Recommended for local development):
   - This error is harmless - it's just Cursor trying to forward the port
   - Your backend will still work fine on localhost:8000
   - Access it directly at `http://localhost:8000` in your browser

2. **Disable port forwarding in Cursor**:
   - Go to Cursor Settings
   - Search for "port forwarding"
   - Disable automatic port forwarding

3. **Use terminal to start backend** (Bypass Cursor):
   ```bash
   cd backend
   python main.py
   ```
   Then access `http://localhost:8000` directly in your browser

4. **Check if port is already in use**:
   ```bash
   # Windows
   netstat -ano | findstr :8000
   
   # Linux/Mac
   lsof -i :8000
   ```

## Backend Not Starting

### Port Already in Use

If you get "Address already in use" error:

1. **Change the port**:
   Create `backend/.env` file:
   ```env
   PORT=8001
   ```
   Then update frontend to use port 8001

2. **Kill the process using port 8000**:
   ```bash
   # Windows
   netstat -ano | findstr :8000
   taskkill /PID <PID> /F
   
   # Linux/Mac
   lsof -ti:8000 | xargs kill
   ```

## Frontend Can't Connect to Backend

### Connection Issues

1. **Verify backend is running**:
   ```bash
   curl http://localhost:8000/api/status
   ```

2. **Check CORS settings**:
   - Backend should allow requests from `http://localhost:3000`
   - Verify `CORSMiddleware` is configured in backend

3. **Check API URL in frontend**:
   - Verify `.env` file has correct `REACT_APP_API_URL`
   - Restart frontend dev server after changing `.env`

4. **Use browser directly**:
   - Open `http://localhost:8000/api/status` in browser
   - Should return JSON response

## Common Issues

### Backend Default Port Changed

The backend now defaults to port **8000** for local development (changed from 7860).

- **Local development**: Port 8000 (default)
- **Hugging Face Spaces**: Port 7860 (set `PORT=7860` in `.env`)

### Environment Variables Not Loading

1. **Check `.env` file location**:
   - Backend `.env` should be in `backend/` directory
   - Frontend `.env` should be in `frontend/` directory

2. **Restart server** after changing `.env`:
   - Backend: Stop and restart `python main.py`
   - Frontend: Stop and restart `npm start`

3. **Verify variable names**:
   - Backend: `PORT`, `GROQ_API_KEY`, etc.
   - Frontend: `REACT_APP_API_URL` (must start with `REACT_APP_`)

## Quick Fixes

### Reset Everything

1. **Stop all servers** (Ctrl+C in terminals)

2. **Start backend**:
   ```bash
   cd backend
   python main.py
   ```
   Should see: `🚀 STARTING VOICE AI ASSISTANT SERVER`

3. **Start frontend** (new terminal):
   ```bash
   cd frontend
   npm start
   ```
   Should open `http://localhost:3000`

4. **Verify connection**:
   - Check browser console for errors
   - Check backend terminal for incoming requests
   - Frontend should show "Connected" status

### Test Backend Directly

```bash
# Test status endpoint
curl http://localhost:8000/api/status

# Test chat endpoint
curl "http://localhost:8000/api/chat?message=Hello"
```

If these work, backend is fine - issue is with frontend connection or Cursor port forwarding.

