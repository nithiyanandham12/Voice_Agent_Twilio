# Frontend Installation Guide

Complete installation and setup guide for the Voice AI Assistant React frontend.

## Prerequisites

- **Node.js 14 or higher** - [Download Node.js](https://nodejs.org/)
- **npm** (comes with Node.js) or **yarn**
- **Backend API** - Make sure the backend server is running (see `../backend/INSTALLATION.md`)

## Step 1: Install Node.js

1. Download Node.js from [nodejs.org](https://nodejs.org/)
2. Install the LTS (Long Term Support) version
3. Verify installation:
```bash
node --version
npm --version
```

You should see version numbers like:
```
v18.17.0
9.6.7
```

## Step 2: Install Dependencies

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install npm packages:
```bash
npm install
```

This will install all required dependencies including:
- React 18.2.0
- React DOM 18.2.0
- React Scripts 5.0.1

## Step 3: Configure Environment Variables

Create a `.env` file in the `frontend` directory:

```env
REACT_APP_API_URL=http://localhost:8000
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REACT_APP_API_URL` | No | Production URL | Backend API URL |

**Note**: All React environment variables must start with `REACT_APP_` prefix.

### For Different Environments

**Local Development:**
```env
REACT_APP_API_URL=http://localhost:8000
```

**Production:**
```env
REACT_APP_API_URL=https://your-backend-domain.com
```

**Custom Backend:**
```env
REACT_APP_API_URL=https://api.example.com
```

## Step 4: Start Development Server

```bash
npm start
```

The application will:
- Start on `http://localhost:3000`
- Automatically open in your default browser
- Hot-reload when you make changes to code

### Development Server Options

**Start on different port:**
```bash
PORT=3001 npm start
```

**Start without opening browser:**
```bash
BROWSER=none npm start
```

## Step 5: Build for Production

Create an optimized production build:

```bash
npm run build
```

This creates a `build` folder with optimized files ready for deployment.

### Build Output

```
frontend/
└── build/
    ├── index.html
    ├── static/
    │   ├── css/
    │   │   └── main.[hash].css
    │   └── js/
    │       └── main.[hash].js
    └── asset-manifest.json
```

### Deploy Build Files

You can deploy the `build` folder to:
- **Netlify** - Drag and drop the build folder
- **Vercel** - Connect your Git repository
- **GitHub Pages** - Use `gh-pages` package
- **Any static hosting** - Upload build folder contents

## Step 6: Verify Installation

1. **Check if frontend is running:**
   - Open `http://localhost:3000` in your browser
   - You should see the Voice AI Assistant interface

2. **Check backend connection:**
   - The frontend will automatically check backend status
   - Look for connection status indicator in the UI
   - If disconnected, verify backend is running and `REACT_APP_API_URL` is correct

3. **Test voice functionality:**
   - Click the microphone button
   - Allow microphone permissions when prompted
   - Speak a message
   - Verify AI response is received

## Browser Compatibility

### Full Support (Recommended)
- **Chrome** (latest) - Best experience
- **Edge** (latest) - Best experience
- **Opera** (latest) - Good support

### Limited Support
- **Firefox** - Limited speech recognition
- **Safari** - Limited speech recognition

### Not Supported
- Internet Explorer

**Recommendation**: Use Chrome or Edge for the best experience with Web Speech API.

## Directory Structure

```
frontend/
├── public/
│   └── index.html          # HTML template
├── src/
│   ├── App.jsx             # Main React component
│   ├── App.css             # Component styles
│   ├── index.js             # React entry point
│   └── index.css            # Global styles
├── build/                   # Production build (generated)
├── node_modules/           # Dependencies (generated)
├── package.json            # Project configuration
├── package-lock.json       # Dependency lock file
├── INSTALLATION.md         # This file
└── .env                    # Environment variables (create this)
```

## Troubleshooting

### Port Already in Use

If port 3000 is already in use:

```bash
# Option 1: Use different port
PORT=3001 npm start

# Option 2: Kill process on port 3000
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:3000 | xargs kill
```

### Module Not Found Errors

Clear cache and reinstall:

```bash
# Remove node_modules and lock file
rm -rf node_modules package-lock.json

# Reinstall
npm install
```

### Backend Connection Issues

1. **Verify backend is running:**
```bash
curl http://localhost:8000/api/status
```

2. **Check CORS settings:**
   - Backend should allow requests from `http://localhost:3000`
   - Verify `CORSMiddleware` is configured in backend

3. **Verify API URL:**
   - Check `.env` file has correct `REACT_APP_API_URL`
   - Restart development server after changing `.env`

### Microphone Not Working

1. **Check browser permissions:**
   - Click the lock icon in address bar
   - Allow microphone access
   - Refresh the page

2. **Browser compatibility:**
   - Use Chrome or Edge for best support
   - Firefox/Safari have limited Web Speech API support

3. **HTTPS requirement:**
   - Some browsers require HTTPS for microphone access
   - Use HTTPS in production or localhost for development

### Build Errors

1. **Clear build cache:**
```bash
rm -rf build
npm run build
```

2. **Check Node.js version:**
```bash
node --version  # Should be 14+
```

3. **Update dependencies:**
```bash
npm update
```

### Environment Variables Not Working

1. **Restart development server** after changing `.env`
2. **Verify variable names** start with `REACT_APP_`
3. **Check for typos** in variable names
4. **Clear browser cache** if needed

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm start` | Start development server |
| `npm run build` | Create production build |
| `npm test` | Run tests |
| `npm run eject` | Eject from Create React App (irreversible) |

## Development Tips

### Hot Reloading
- Changes to `.jsx` and `.css` files automatically reload
- No need to refresh browser manually

### Browser DevTools
- Press `F12` to open developer tools
- Check Console for errors and logs
- Use Network tab to monitor API calls

### Debugging
- Use `console.log()` for debugging
- Check browser console for errors
- Verify API responses in Network tab

## Production Deployment

### Option 1: Static Hosting (Recommended)

**Netlify:**
1. Drag and drop `build` folder to Netlify
2. Or connect Git repository
3. Set build command: `npm run build`
4. Set publish directory: `build`

**Vercel:**
1. Connect Git repository
2. Framework preset: Create React App
3. Deploy automatically

### Option 2: Custom Server

Serve `build` folder with any static file server:
- Nginx
- Apache
- Express.js static middleware
- Python http.server

### Option 3: Docker

Create a Dockerfile:
```dockerfile
FROM nginx:alpine
COPY build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Next Steps

- Connect to your backend API
- Configure Twilio settings in the UI
- Test voice conversation functionality
- Deploy to production

## Support

For issues or questions:
- Check browser console for errors
- Verify backend is running and accessible
- Review backend installation guide: `../backend/INSTALLATION.md`
- Check main README.md for project overview

