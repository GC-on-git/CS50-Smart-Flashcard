# Smart Flashcard Application

#### Video Demo:  <URL HERE>

#### Description:

Smart Flashcard Application is a full-stack web application designed to optimize learning and memory retention through intelligent spaced repetition. The application implements the proven SM-2 (SuperMemo 2) algorithm to automatically schedule flashcard reviews based on individual user performance, ensuring that difficult cards are reviewed more frequently while mastered content appears less often.

## What This Project Does

The Smart Flashcard Application is a sophisticated learning platform that combines cognitive science principles with modern web technologies to create an efficient study tool. At its core, the application manages multiple-choice question (MCQ) flashcards organized into decks, tracks user performance, and uses an adaptive scheduling algorithm to optimize review timing for maximum retention.

The system automatically calculates when each flashcard should be reviewed again based on how well users remember the content. Cards answered correctly are scheduled for later review with increasing intervals, while difficult cards appear more frequently until mastered. This approach, based on decades of memory research, has been proven to significantly improve long-term retention compared to traditional study methods.

The application provides a complete learning ecosystem with user authentication, deck organization, AI-powered card generation, progress tracking, statistics, and study sessions with keyboard shortcuts for efficient review.

## Features

### Core Functionality
- **Spaced Repetition Algorithm (SM-2)**: Automatically schedules card reviews based on user performance using the SuperMemo 2 algorithm
- **Multiple-Choice Question Format**: All flashcards use MCQ format with 4 options and 1 correct answer
- **Deck Management**: Create, edit, archive, duplicate, and delete flashcard decks with titles and descriptions
- **Card Management**: Full CRUD operations for individual flashcards with options and explanations
- **AI-Powered Card Generation**: Generate flashcards from topic descriptions using OpenRouter API (supports GPT-3.5, GPT-4, Claude, Gemini, and other models)
- **Study Sessions**: Interactive review interface with MCQ format, progress tracking, and adaptive scheduling
- **Due Cards Tracking**: Monitor how many cards are due for review in each deck
- **Study Modes**: Normal mode and hard mode for reviewing difficult cards
- **Keyboard Shortcuts**: Navigate and answer cards using number keys (1-4) and arrow keys

### User Engagement Features
- **Daily Streaks**: Track consecutive days of study to build learning habits
- **Session Streaks**: Track consecutive correct answers during study sessions
- **Statistics Dashboard**: View comprehensive learning statistics including:
  - Overall progress and review counts
  - Per-deck statistics and performance metrics
  - Review timeline and learning trends
  - Difficult cards identification
- **User Preferences**: Customizable settings for personalized experience

### Technical Features
- **JWT Authentication**: Secure user authentication with access and refresh tokens
- **RESTful API**: Well-structured API with comprehensive endpoints for all operations
- **Search & Filter**: Search decks and cards by title, description, or content
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Error Handling**: Robust error handling with user-friendly error messages
- **Data Validation**: Input validation using Pydantic schemas
- **Database Migrations**: Alembic-based database migrations for schema management

## How to Use as a Developer

### Prerequisites
- **Backend**: Python 3.10 or higher, PostgreSQL (or SQLite for development), pip
- **Frontend**: Node.js 16 or higher, npm or yarn

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd cs50/backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   Create a `.env` file in `cs50/backend/` with:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/flashcard_db
   # Or for SQLite: DATABASE_URL=sqlite:///./flashcard.db
   SECRET_KEY=your-secret-key-here-change-in-production
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   AI_API_KEY=your-openrouter-api-key-here  # Optional, for AI card generation
   AI_MODEL=openai/gpt-3.5-turbo  # Optional, default AI model
   ```

5. Initialize the database:
   ```bash
   alembic upgrade head
   ```

6. Start the development server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd cs50/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:3000`

### Running Both Services

You'll need two terminal windows:
- **Terminal 1** (Backend): Run `uvicorn app.main:app --reload` from `cs50/backend/`
- **Terminal 2** (Frontend): Run `npm run dev` from `cs50/frontend/`

### Development Tools

- **Testing**: Run `pytest` from `cs50/backend/` to execute the test suite
- **Code Formatting**: Uses Black and Ruff for Python code formatting and linting
- **Type Checking**: TypeScript provides type safety for frontend code
- **Database Migrations**: Use Alembic to create and manage database migrations

### Demo Data

Load sample data for testing:
```bash
# From project root
python cs50/backend/scripts/load_demo_data_mcq.py
```

Or with custom credentials:
```bash
python cs50/backend/scripts/load_demo_data_mcq.py your_email@example.com your_password
```

Default credentials: `demo@example.com` / `demopassword123`

## How to Use as an End User

### Getting Started

1. **Registration**: Create a new account with email, username, and password
2. **Login**: Sign in with your credentials to access your dashboard

### Creating and Managing Decks

1. **Create a Deck**: Click "Create New Deck" on the dashboard, enter a title and optional description
2. **View Decks**: All your decks appear on the dashboard with due card counts
3. **Search Decks**: Use the search bar to filter decks by title or description
4. **Edit Decks**: Click on a deck to view and manage its cards
5. **Archive Decks**: Archive decks you want to keep but not actively study
6. **Delete Decks**: Remove decks you no longer need

### Creating Flashcards

1. **Manual Creation**: 
   - Open a deck and click "Add New Card"
   - Enter a question, 4 answer options (mark one as correct), and an explanation
   - Save the card

2. **AI Generation**:
   - Click "Generate Cards with AI" in a deck
   - Enter a topic description (e.g., "Python data structures")
   - Specify the number of cards to generate (1-20)
   - The AI creates MCQ flashcards with proper formatting
   - Review and save the generated cards

3. **Duplicate Cards**: Clone existing cards to create variations or similar questions

### Studying Flashcards

1. **Start a Study Session**:
   - Click "Study" on any deck with due cards
   - Or navigate to a deck and click "Study Due Cards"

2. **Answer Questions**:
   - Read the question carefully
   - Select one of the 4 multiple-choice options
   - View immediate feedback showing if you answered correctly
   - Read the explanation to understand the concept

3. **Study Modes**:
   - **Normal Mode**: Studies all due cards
   - **Hard Mode**: Focuses on difficult cards that need extra practice

4. **Keyboard Shortcuts**:
   - Press `1`, `2`, `3`, or `4` to select answer options
   - Use arrow keys to navigate between cards
   - Space bar to continue after viewing results

5. **Track Progress**:
   - View progress bar showing cards completed
   - See session streak (consecutive correct answers)
   - Monitor daily streak for consistent study habits

### Understanding Spaced Repetition

- **Easy Cards**: Cards you answer correctly will appear less frequently (intervals increase)
- **Difficult Cards**: Cards you struggle with will appear more often until mastered
- **Due Cards**: Cards scheduled for review based on your past performance
- **Next Review Date**: Each card shows when it will next appear for review

### Viewing Statistics

1. **Statistics Page**: Navigate to the Statistics page from the dashboard
2. **Overview**: See total reviews, cards mastered, and overall progress
3. **Deck Statistics**: View performance metrics for each deck
4. **Review Timeline**: Track your study activity over time
5. **Difficult Cards**: Identify cards that need extra attention

### Managing Account

1. **Settings**: Access user preferences and account settings
2. **Profile**: View your account information
3. **Logout**: Sign out securely from your account

### Best Practices

- **Regular Study**: Maintain your daily streak by studying consistently
- **Create Focused Decks**: Organize cards by topic for better learning
- **Review Explanations**: Always read explanations to deepen understanding
- **Use AI Generation**: Leverage AI to quickly create comprehensive study sets
- **Monitor Statistics**: Track your progress to identify areas needing improvement
- **Focus on Difficult Cards**: Use hard mode to concentrate on challenging material