# Smart Flashcard Application

#### Video Demo:  <URL HERE>

#### Description:

The Smart Flashcard Application is a full-stack web application designed to optimize learning. I built it with FastAPI, React, and threw in some AI magic :) The app uses the SM-2 (SuperMemo 2) spaced repetition algorithm, which basically means it figures out which cards you're struggling with and shows them to you more often, while letting you breeze through the easy stuff. This is done to automatically schedule flashcard reviews based on individual user performance, ensuring that difficult cards are reviewed more frequently while easy content appears less often.

The application provides a complete learning ecosystem with user authentication, deck organization, AI-powered card generation, progress tracking, statistics, and study sessions with keyboard shortcuts for efficient review. All flashcards use a multiple-choice question (MCQ) format with four options and one correct answer, making the learning experience consistent and measurable.

## Architecture Overview

The application follows a clean separation between backend and frontend. The backend is built with FastAPI, SQLAlchemy for database operations, and PostgreSQL. The frontend is a React application with TypeScript for type safety, using React Router for navigation and a custom API client for backend communication.

## Backend Files and Their Purposes

**`app/main.py`**: The FastAPI application entry point that initializes the application, configures CORS middleware for frontend communication, and registers all API routers. It serves as the central hub connecting authentication, user management, decks, cards, preferences, and statistics endpoints.

**`app/models/`**: Contains SQLAlchemy ORM models defining the database schema. `user.py` defines the User model with authentication fields. `deck.py` represents flashcard collections with title, description, and archive status. `card.py` contains three models: `Card` (the flashcard itself), `CardOption` (the four multiple-choice options with one marked as correct), and `FlashcardReview` (tracks every review attempt with timing and correctness data for analytics). `streak.py` manages user streaks for gamification, and `user_preferences.py` stores user settings.

**`app/schemas/`**: Pydantic schemas for request/response validation and serialization. These ensure type safety and data validation. Each model has corresponding schemas for creation, updates, and responses.

**`app/routers/`**: FastAPI route handlers organized by domain. `auth/routes.py` handles registration, login, token refresh, and profile retrieval using JWT authentication. `users.py` manages user CRUD operations. `decks.py` provides endpoints for deck CRUD operations. `cards.py` handles card CRUD operations. `preferences.py` manages user settings, and `statistics.py` aggregates learning data for the dashboard.

**`app/services/`**: Where all the actual logic lives, separate from the routes. `scheduling.py` has the SM-2 algorithm - it figures out quality scores from how fast you answer and whether you got it right, then updates when cards are due. Quick correct answers (<5s) = quality 5, medium speed (5-15s) = quality 4, slow but correct (>15s) = quality 3, wrong answers = quality 1. `ai_generator.py` talks to OpenRouter API to generate flashcards from topic descriptions. I had to add a lot of validation because the AI sometimes messes up the format. `crud_cards.py`, `crud_decks.py`, and `crud_users.py` handle all the database operations. `streaks.py` manages both session streaks (consecutive correct answers) and daily streaks (consecutive study days). `statistics.py` pulls together all the review data for analytics.

**`app/auth/`**: Authentication stuff. `jwt_handler.py` creates and validates JWT tokens, `password_utils.py` hashes passwords with bcrypt, and `routes.py` has the auth endpoints. `oauth.py` has some OAuth setup for Google/GitHub but I haven't finished that yet.

**`app/core/`**: Core configuration and dependencies. `config.py` uses Pydantic Settings to load environment variables for database URLs, JWT secrets, AI API keys, and algorithm parameters. `dependencies.py` provides FastAPI dependencies like `get_current_active_user` for authentication. `security.py` contains security utilities.

**`app/db/`**: Database setup. `session.py` configures SQLAlchemy engine and sessions. The `migrations/` folder has Alembic migrations for managing schema changes.

**`scripts/load_demo_data_mcq.py`**: Utility script to populate the database with sample MCQ flashcards for testing and demonstration purposes.

## Frontend Files and Their Purposes

**`src/App.tsx`**: The main React component that sets everything up - routing, auth state, context providers. It checks if you're logged in when the app loads and redirects to login if you're not.

**`src/pages/`**: All the main pages. `Login.tsx` and `Register.tsx` handle sign in/sign up with form validation. `Dashboard.tsx` shows all your decks, lets you search them, see how many cards are due, and manage decks (create, edit, archive, delete). `DeckDetail.tsx` shows all cards in a deck - you can add, edit, delete, duplicate cards, or generate new ones with AI. `StudySession.tsx` is where the magic happens - shows cards one at a time, tracks how long you take, sends answers to the backend, updates your progress, and handles keyboard shortcuts. `Statistics.tsx` shows all your learning stats with charts. `Settings.tsx` is for user preferences.

**`src/components/`**: Reusable UI components. `Modal.tsx` is a flexible modal system I built. `Toast.tsx` and `ToastContainer.tsx` handle toast notifications (those little popup messages). `LoadingSkeleton.tsx` shows loading states while data is fetching.

**`src/contexts/`**: React contexts for global state. `ThemeContext.tsx` manages the theme (though dark mode isn't fully done yet). `ToastContext.tsx` provides a toast system that works everywhere in the app.

**`src/api/client.ts`**: My API client that wraps all the fetch calls. It automatically adds JWT tokens to requests and handles token refresh. All the API methods are type-safe.

**`src/hooks/useKeyboardShortcuts.ts`**: Custom hook for keyboard shortcuts in study sessions. You can press 1-4 to select answers, arrow keys to navigate, spacebar to continue. The tricky part was making sure it doesn't trigger when you're typing in a form field.

**`src/types/index.ts`**: TypeScript type definitions matching backend schemas, ensuring type safety across the frontend.

## Design Choices and Rationale

**MCQ Format**: I went with multiple-choice questions (4 options, 1 correct answer) instead of free-form answers. It makes the UI way simpler, validation is straightforward, and gives consistent data for the SM-2 algorithm. While traditional flashcards with free-form answers are more flexible, MCQs enable faster review sessions and objective performance measurement.

**SM-2 Algorithm Implementation**: SM-2 is a classic spaced repetition algorithm. It's simpler than newer versions like SM-17, but it works really well. I automated the quality calculation using both correctness and response time - so if you answer fast and correctly, that's different from answering slowly but correctly. This gives the algorithm better info to schedule reviews.

**Response Time Tracking**: I track response time for each answer to calculate quality scores. This required careful implementation in the frontend to measure time from when a card is displayed until an answer is submitted, accounting for time spent reading explanations. The backend stores response times in milliseconds, enabling future analytics on learning patterns.

**Separate Services Layer**: I separated business logic into a `services/` directory rather than putting it directly in routers. This separation makes the code more testable, reusable, and maintainable. For example, the SM-2 algorithm logic in `scheduling.py` can be tested independently of HTTP concerns.

**JWT with Refresh Tokens**: I implemented JWT authentication with separate access and refresh tokens. Access tokens expire after 30 minutes for security, while refresh tokens allow seamless session extension. This balances security (short-lived access tokens) with user experience (no frequent re-logins).

**OpenRouter for AI Generation**: Instead of directly using OpenAI's API, I chose OpenRouter which provides access to multiple AI models (GPT-3.5, GPT-4, Claude, Gemini) through a single interface. This gives users flexibility to choose models based on cost and quality preferences. The AI generation includes extensive validation to ensure generated cards meet the MCQ format requirements.

**Database Schema with Reviews Table**: I made a separate `FlashcardReview` table to track every single review attempt, not just update the card. This lets me do cool analytics (response times, trends, finding hard cards) while keeping the `Card` table simple. Yeah, it uses more storage, but queries are way faster.

**Keyboard Shortcuts**: Added keyboard navigation for study sessions - you can answer and navigate without touching the mouse. Makes rapid reviews possible. The hook had to be smart about not triggering when you're typing in forms.

**TypeScript Throughout Frontend**: Used TypeScript everywhere in the frontend. Catches bugs at compile time and makes development way smoother. The types match the backend schemas so everything stays in sync.

## Design Process and Development Journey

This project evolved a lot from my initial idea to what it is now. I built it iteratively, trying things out and refining as I went. Here's how it all came together:

### Phase 1: Requirements Gathering and Planning

I wanted to build something for exam prep and revision. My initial plan was pretty simple - just user login, basic flashcards with front and back, and decks to organize them. That was it!

### Phase 2: Database Schema Design

Initially, I considered a simpler schema with just Users, Decks, and Cards. However, after researching , I realised I needed spaced repetition implementations. I went ahead with SM-2 algorithm whose parameters I tracked directly with cards.

A critical design decision was creating a separate `FlashcardReview` table rather than just updating card state. This emerged from recognizing that analytics and statistics would be valuable features. By storing every review attempt with timestamps, response times, and correctness, I could build rich statistics dashboards without complex queries. This denormalization decision trades storage space for query performance and analytical capabilities.

The schema uses a `flashcards` namespace to organize all tables, and implements proper foreign key constraints with CASCADE deletes to maintain data integrity. The current migration file shows the complete schema. But this was reached after various different implementations, and iterations demonstrating careful planning before final implementation.

### Phase 3: Backend Architecture Development

The backend architecture follows a layered approach, developed incrementally:

**Authentication Layer**: Started with basic JWT auth, using bcrypt for password hashing. Then I realized that 30-minute token expiration would be super annoying - users would have to log in constantly. So I added refresh tokens to keep sessions going smoothly while still being secure. I also set it up so I can add OAuth (Google/GitHub) later if I want.

**API Design**: I organized routes by domain following RESTful principles. Each router handles HTTP concerns (request validation, response formatting) while delegating business logic to a service layer.

**Service Layer**: The services directory was created to separate business logic from route handlers. `ai_generator.py` was separated because AI integration involves complex prompt engineering and response validation that shouldn't clutter route handlers.

**Error Handling**: Throughout development, I refined error handling to provide meaningful error messages. Initially, errors were generic, but testing revealed that specific error messages (e.g., "Email already registered" vs. "Registration failed") significantly improve the experience.

### Phase 4: SM-2 Algorithm Implementation

The SM-2 algorithm implementation was the most technically challenging aspect. I started by studying the original SuperMemo 2 algorithm specification, initially implementing it for normal QnA format with user feedback. Later, this evolved to use timer-based tracking and MCQ responses.

**Quality Score Calculation**: The original SM-2 uses user-provided quality scores (0-5). Initially, I implemented this with manual user feedback in a QnA format. Later, I automated this by analyzing response time and correctness. This required experimentation with time thresholds. Initially, I used simple thresholds, but testing revealed that 5 seconds for "fast" and 15 seconds for "medium" provided good differentiation between confident recall and hesitant recall.

**Interval Calculation**: The algorithm's interval calculation logic required careful implementation. I tested edge cases: first review (repetitions=0), second review (repetitions=1), and subsequent reviews. The ease factor adjustment formula needed precise implementation to match the original algorithm's behavior.

**Due Cards Query**: Getting due cards efficiently took some thought. Cards are due if `next_review` is NULL (never reviewed) or `next_review <= now()`. I order by `next_review` with NULLs first, so new cards show up first, then overdue ones in order.

### Phase 5: AI Card Generation Integration

The AI card generation feature was added after the core functionality was stable. I chose OpenRouter over direct OpenAI integrationso that iI can test using free models. The major consideration here was cost. The implementation required extensive prompt engineering to ensure the AI generates valid MCQ format cards.

**Prompt Development**: I iteratively refined the AI prompt through testing. 

**Response Validation**: The AI response validation logic was developed through trial and error. Initially, I trusted the AI output, but testing revealed occasional format issues. The current implementation includes multiple validation layers: JSON parsing, structure validation, option count verification etc. 

### Phase 6: Frontend Architecture and User Experience

The frontend went through a big evolution. I started with basic HTML, CSS, and JavaScript - just to get something working. It was a proof of concept, but as the app grew, I needed something more robust. Thats where the LLMs came in to help.

**Migration to React**: I migrated everything to React using basic knowledge and some good prompting- for better UX, smoother animations, and a nicer-looking page. 

**Authentication Flow**: Set up token-based auth that checks if you're logged in when the app loads. I store tokens in localStorage (not sessionStorage) so you stay logged in across browser sessions. Added token refresh logic so expired tokens get renewed automatically.

**State Management**: Used React Context for global state (toasts, theme) instead of Redux. The app's state needs are pretty simple, so Context is enough without the extra complexity.

**Study Session Interface**: The study page needed careful UX work. I made it show one card at a time instead of dumping everything on screen - way less overwhelming.

**Keyboard Shortcuts**: Added keyboard navigation after I realized mouse-only was too boring. Made a `useKeyboardShortcuts` hook to handle it all.

**Loading States**: Added loading skeletons throughout the app. At first pages just showed blank screens while loading, which felt super slow. Skeletons give visual feedback that something's happening, way better UX.

### Phase 7: Gamification and Engagement Features

Added streak tracking to make it more engaging. I got this idea while doing my daily Duolingo lessons - thank you big green owl.

**Statistics Dashboard**: Built this incrementally. Started with basic counts (total cards, reviews), then added per-deck stats, review timelines, and finally finding difficult cards. Each part needed new database queries and aggregation. The stats service uses SQLAlchemy's query builder to aggregate efficiently without loading everything into memory.

### Phase 8: Documentation and Polish

Final phase was all about documentation, error messages, and polish. Added docstrings to all functions explaining what they do, parameters, return values, etc. This README documents not just how to use it, but why I made certain decisions and how it all came together.

**Error Messages**: Refined error messages to be user-friendly. Instead of "Database constraint violation," users see "Email already registered" or "Deck not found." Way more helpful!

**UI Polish**: Added consistent styling, dark and light themes, loading states, toast notifications for actions, and confirmation dialogs for destructive stuff. These little details make it feel way more polished and professional.

### Key Learnings and Iterations

A bunch of features changed a lot from how I first built them:

1. **Response Time Tracking**: At first I only tracked if you got it right or wrong. Adding response time meant refactoring the study session to measure time accurately and updating the SM-2 quality calculation.

2. **AI Generation Validation**: Early AI generation was pretty unreliable. I had to add tons of validation and error handling to make it work even when the AI messes up.

3. **Streak Logic**: The daily streak I settled on is one that's achievable and makes sense.

4. **Database Schema**: The reviews table came later - I added it when I realized analytics would be cool. 

5. **Frontend State Management**: Started with local state in components, but moved to Context for global stuff (toasts, theme) to make it more maintainable.

The whole process was super iterative - I'd build something, test it, realize it could be better, and refine it. The modular architecture I set up early on made it easy to add and change features without huge refactors. Definitely learned the value of good initial design!

## Final Features

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