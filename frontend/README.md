# Voice AI Assistant - React Frontend

This is the React frontend for the Voice AI Assistant application.

## Features

- One-click voice conversation mode
- Real-time speech recognition (Web Speech API)
- Real-time text-to-speech (Web Speech API)
- Conversation history with localStorage persistence
- Business-centric UI design
- Status indicators for call state

## Prerequisites

- Node.js (v14 or higher)
- npm or yarn

## Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

## Running the Application

1. Make sure the backend API is running on `http://localhost:8000`

2. Start the React development server:
```bash
npm start
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser (Chrome or Edge recommended for best speech recognition support)

## Building for Production

```bash
npm run build
```

This creates an optimized production build in the `build` folder.

## Environment Variables

You can create a `.env` file in the `frontend` directory to customize the API URL:

```
REACT_APP_API_URL=http://localhost:8000
```

## Browser Support

- Chrome/Edge: Full support for speech recognition and synthesis
- Firefox: Limited speech recognition support
- Safari: Limited speech recognition support

For best results, use Chrome or Edge browser.

