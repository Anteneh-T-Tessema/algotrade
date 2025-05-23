# Local Development Guide

This guide provides instructions for running the crypto trading platform locally for development purposes.

## Prerequisites

- Python 3.8+ with pip
- Node.js 16+ with npm
- Git

## Setup

### 1. Clone the Repository (if you haven't already)

```bash
git clone <repository-url>
cd botsalgo
```

### 2. Python Environment Setup

Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

### 3. Frontend Setup

Navigate to the web dashboard directory:

```bash
cd web_dashboard
```

Install Node.js dependencies:

```bash
npm install
```

## Running the Application Locally

### Option 1: Using the Development Script (Recommended)

Run the development script from the web_dashboard directory:

```bash
./dev.sh
```

This script will:
- Activate the Python virtual environment
- Install dependencies if needed
- Start the backend server on port 8000
- Start the frontend development server
- Set up proper development environment variables

### Option 2: Manual Startup

#### Terminal 1 - Backend Server:

```bash
cd web_dashboard
source ../venv/bin/activate  # On Windows: ..\venv\Scripts\activate
export NODE_ENV=development  # On Windows: set NODE_ENV=development
python run_server.py
```

#### Terminal 2 - Frontend Server:

```bash
cd web_dashboard
export REACT_APP_API_URL=http://localhost:8000/v1  # On Windows: set REACT_APP_API_URL=http://localhost:8000/v1
npm start
```

## Accessing the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/v1
- **API Documentation**: http://localhost:8000/docs

## WebSocket Endpoints (for development)

- Market Data: `ws://localhost:8000/v1/ws/market/{client_id}`
- Order Book: `ws://localhost:8000/v1/ws/orderbook/{client_id}`
- Portfolio: `ws://localhost:8000/v1/ws/portfolio/{client_id}`
- Trades: `ws://localhost:8000/v1/ws/trades/{client_id}`

## Development Notes

- The application uses SQLite for local development instead of a production database
- Authentication is disabled in development mode for easier testing
- Mock data is enabled by default for development

## Troubleshooting

### WebSocket Connection Issues

If you experience WebSocket connection issues:

1. Check that both servers are running
2. Ensure your browser supports WebSockets
3. Check browser console for error messages
4. Try a different browser if issues persist

### API Connection Issues

If the frontend cannot connect to the API:

1. Verify that the backend server is running
2. Check that CORS is properly configured
3. Ensure the REACT_APP_API_URL environment variable is set correctly

## Next Steps

After successful local testing, you can:

1. Build the frontend for production: `npm run build`
2. Test the production build locally
3. Containerize the application using Docker
4. Deploy to cloud services
