# AI Email Assistant

An intelligent email management application powered by AI. This application provides a ChatGPT-like interface for managing Gmail emails with features like AI-powered summaries, smart reply generation, email categorization, and natural language command processing.

**💡 FREE AI Option Available!** This project supports both **Google Gemini (FREE)** and **OpenAI** - switch with one environment variable!

## 🌟 Live Demo

**Frontend URL:** `https://your-app-name.vercel.app` (Update after deployment)
**Backend URL:** `https://your-backend-url.vercel.app` (Update after deployment)

## 🚀 Features

### Core Features
- ✅ **Google OAuth2 Authentication** - Secure login with Gmail permissions
- ✅ **AI Email Summaries** - Automatic summarization of email content using GPT-4o-mini
- ✅ **Smart Reply Generation** - Context-aware, professional email responses
- ✅ **Email Management** - Read, reply to, and delete emails directly from the interface
- ✅ **Natural Language Commands** - Interact naturally: "Show me my latest emails", "Give me today's digest"

### Bonus Features Implemented
- ✅ **Smart Categorization** - Automatically categorize emails into Work, Personal, Promotions, and Urgent
- ✅ **Daily Digest** - AI-generated summary of the day's emails with action items
- ✅ **Natural Language Processing** - Intent classification for flexible user commands
- ✅ **Dual AI Provider Support** - Works with FREE Google Gemini OR OpenAI (configurable)
- ✅ **Comprehensive Logging** - Full observability for all operations
- ✅ **Error Handling & Resilience** - Graceful handling of API failures and expired sessions
- ✅ **Automated Tests** - pytest test suite for backend core logic

## 🛠️ Tech Stack

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Authentication:** Google OAuth2 with JWT sessions
- **Email Integration:** Gmail API
- **AI Provider:** Google Gemini (FREE!) OR OpenAI GPT-4o-mini (configurable)
- **Testing:** pytest with async support

### Frontend
- **Framework:** Next.js 14 (App Router, TypeScript)
- **Styling:** Tailwind CSS
- **UI Components:** Shadcn/UI (Radix UI primitives)
- **State Management:** React hooks
- **HTTP Client:** Axios

### Deployment
- **Platform:** Vercel (Frontend & Backend)
- **Backend Runtime:** Python 3.11 on Vercel Serverless Functions

## 📋 Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- npm or yarn
- Google Cloud Platform account (for OAuth credentials)
- **AI Provider (choose one):**
  - **Google Gemini** (FREE!) - Get key at [Google AI Studio](https://makersuite.google.com/app/apikey) 🌟 RECOMMENDED
  - **OpenAI** (Paid) - Get key at [OpenAI Platform](https://platform.openai.com/api-keys)

## 🔧 Local Development Setup

### Step 1: Clone the Repository

```bash
git clone <your-repo-url>
cd constructure-ai
```

### Step 2: Configure Google OAuth2

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Gmail API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API" and click "Enable"
4. Create OAuth2 Credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Web application"
   - Add Authorized Redirect URIs:
     - `http://localhost:8000/auth/callback` (for local development)
     - `https://your-backend-url.vercel.app/auth/callback` (for production)
5. Configure OAuth Consent Screen:
   - Add your app information
   - **IMPORTANT:** Under "Test users", add: `test@gmail.com` or `testingcheckuser1234@gmail.com`
6. Copy your **Client ID** and **Client Secret**

### Step 3: Get AI API Key

**Option A: Google Gemini (FREE) - Recommended! 🎉**

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key (starts with `AIzaSy...`)
4. **No payment required!** See [GEMINI_SETUP.md](GEMINI_SETUP.md) for details

**Option B: OpenAI (Paid)**

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Copy the key (it will only be shown once)
4. You'll need to change `AI_PROVIDER=openai` in `.env`

### Step 4: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp ../.env.example .env

# Edit .env and fill in your credentials:
# - GOOGLE_CLIENT_ID
# - GOOGLE_CLIENT_SECRET
# - JWT_SECRET_KEY (generate a random string)
# - AI_PROVIDER=gemini (or openai)
# - GEMINI_API_KEY (if using Gemini - FREE!)
# - OPENAI_API_KEY (if using OpenAI - paid)
```

### Step 5: Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

### Step 6: Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
# Make sure virtual environment is activated
python main.py
# Backend will run on http://localhost:8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
# Frontend will run on http://localhost:3000
```

### Step 7: Test the Application

1. Open your browser and navigate to `http://localhost:3000`
2. Click "Sign in with Google"
3. Authorize the application with your Google account
4. You'll be redirected to the dashboard
5. Try commands like:
   - "Show me my latest emails"
   - "Give me today's digest"
   - "Categorize my emails"

## 🧪 Running Tests

```bash
cd backend

# Make sure virtual environment is activated
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_auth_service.py
```

## 🚀 Deployment to Vercel

### Prerequisites for Deployment
1. Vercel account ([sign up here](https://vercel.com/signup))
2. Vercel CLI installed: `npm install -g vercel`

### Step 1: Update Environment Variables for Production

Create `.env.production` files with your production URLs and credentials.

### Step 2: Deploy Backend

```bash
cd backend
vercel --prod
# Follow the prompts and note the deployed URL
```

### Step 3: Deploy Frontend

```bash
cd frontend
# Set environment variable for production API URL
vercel env add NEXT_PUBLIC_API_URL
# Enter your backend URL: https://your-backend-url.vercel.app

vercel --prod
# Note the deployed URL
```

### Step 4: Update Google OAuth Redirect URIs

1. Go back to Google Cloud Console
2. Add your production redirect URI:
   - `https://your-backend-url.vercel.app/auth/callback`
3. Update your `.env` variables with production URLs

### Step 5: Update Frontend Environment

Update the frontend environment variables in Vercel dashboard:
- `NEXT_PUBLIC_API_URL` should point to your backend URL

## 📁 Project Structure

```
constructure-ai/
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py              # Configuration management
│   ├── requirements.txt       # Python dependencies
│   ├── services/
│   │   ├── auth_service.py    # OAuth2 & JWT handling
│   │   ├── gmail_service.py   # Gmail API integration
│   │   └── ai_service.py      # OpenAI integration
│   └── tests/                 # pytest test suite
│       ├── test_auth_service.py
│       ├── test_gmail_service.py
│       └── test_ai_service.py
├── frontend/
│   ├── app/
│   │   ├── page.tsx           # Login page
│   │   ├── dashboard/
│   │   │   └── page.tsx       # Main dashboard
│   │   ├── layout.tsx         # Root layout
│   │   └── globals.css        # Global styles
│   ├── components/
│   │   ├── ui/                # Shadcn UI components
│   │   ├── EmailCard.tsx      # Email display component
│   │   ├── ChatMessage.tsx    # Chat message component
│   │   └── CategoryView.tsx   # Email categorization view
│   ├── lib/
│   │   ├── api.ts            # API client
│   │   └── utils.ts          # Utility functions
│   ├── package.json
│   └── tsconfig.json
├── vercel.json               # Vercel deployment config
├── .env.example             # Environment variables template
└── README.md               # This file
```

## 🔐 Security Considerations

- **JWT Tokens:** Stored securely in HttpOnly cookies and localStorage
- **OAuth2 Flow:** Follows Google's recommended security practices
- **API Keys:** Never exposed to the frontend; managed server-side
- **CORS:** Configured to allow only trusted origins
- **Input Validation:** All user inputs are validated and sanitized

## 🐛 Troubleshooting

### "Authentication Failed"
- Verify Google OAuth credentials are correct
- Check that redirect URIs match exactly in Google Console
- Ensure test users are added in OAuth consent screen

### "Failed to fetch emails"
- Check that Gmail API is enabled in Google Cloud Console
- Verify the user has granted all required permissions
- Check backend logs for specific error messages

### "AI features not working"
- Verify OpenAI API key is valid and has credits
- Check the model name is correct (gpt-4o-mini)
- Review backend logs for API errors

### Backend not starting
- Ensure Python 3.11+ is installed
- Verify all environment variables are set in .env
- Check that all dependencies are installed: `pip install -r requirements.txt`

### Frontend build errors
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Verify Node.js version is 18+
- Check that .env.local has NEXT_PUBLIC_API_URL set

## 📝 API Documentation

Once the backend is running, visit:
- **Interactive API Docs:** `http://localhost:8000/docs`
- **Alternative Docs:** `http://localhost:8000/redoc`

## 🤝 Contributing

This is a technical assessment project, but suggestions are welcome!

## 📄 License

This project is created as part of a technical assessment for Constructure AI.

## 📞 Support

For issues or questions, please contact [your-email@example.com]

---

## 🎯 Assignment Completion Checklist

### Part 0 - Deployment ✅
- [x] Frontend deployed to Vercel
- [x] Backend accessible by frontend
- [x] Test user added to Google OAuth

### Part 1 - Google Authentication ✅
- [x] Google OAuth2 login implemented
- [x] Gmail permissions requested (read, send, delete)
- [x] Session persistence with JWT
- [x] Error handling for failed logins, revoked permissions, expired sessions

### Part 2 - Chatbot Dashboard ✅
- [x] User greeting with Google profile information
- [x] Capability explanation on first load
- [x] Conversation thread with user/AI messages
- [x] Clean, professional UI

### Part 3 - Email Automation ✅
- [x] Read last 5 emails with AI summaries
- [x] Generate AI-powered replies
- [x] Send emails with confirmation
- [x] Delete emails with confirmation
- [x] Natural language command understanding

### Part 4 - Bonus Features ✅
- [x] Natural language command processing
- [x] Smart inbox categorization
- [x] Daily digest generation
- [x] Comprehensive logging and observability
- [x] Automated tests (pytest)

---

**Built with ❤️ for Constructure AI**
