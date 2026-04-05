========================================
    FARMER ASSISTANT - PROJECT README
========================================

📌 PROJECT DESCRIPTION
A web application designed to help farmers with crop guidance, market price tracking, and government schemes information. It provides personalized recommendations based on their location, soil type, and farming preferences.

========================================
🎯 KEY FEATURES
========================================

1. USER MANAGEMENT
   - User Registration and Login
   - Admin Dashboard for managing users
   - Profile Management (update personal details)
   - Multi-language support (English, Marathi, Hindi)

2. CROP ADVISORY
   - Get crop recommendations based on:
     * Season (Kharif, Rabi, Zaid)
     * Soil type (Black, Loamy, Clay)
     * Location (State and District)
   - View fertilizer and pest control information for crops

3. MARKET PRICES
   - View current market prices for different crops
   - Track price trends in different districts
   - Admin can update market prices

4. GOVERNMENT SCHEMES
   - Browse available farming schemes
   - Learn about eligibility criteria
   - Find application information

5. FEEDBACK SYSTEM
   - Users can submit feedback
   - Admins can view and manage feedback

6. ACTIVITY TRACKING
   - Track user activities and interactions
   - Admin monitoring dashboard

========================================
⚙️ GETTING STARTED
========================================

STEP 1: INSTALL DEPENDENCIES
- Open terminal/command prompt in project folder
- Run: pip install -r requirements.txt

STEP 2: SET UP DATABASE
- First time setup only
- Run: python setup_database.py
- This creates all database tables and adds sample data

STEP 3: RUN THE APPLICATION
- Run: python app.py
- Open browser and go to: http://localhost:5000
- Login with credentials:
  * User Mobile: any registered number
  * Admin Username: admin
  * Admin Password: admin

========================================
📁 PROJECT STRUCTURE
========================================

Project FA/
├── app.py                    # Main application file (Flask app)
├── db.py                     # Database setup and connection
├── config.py                 # Configuration settings
├── utils.py                  # Helper functions
├── crop_logic.py             # Crop recommendation logic
├── setup_database.py         # Initial database setup
├── seed_market_prices.py     # Add sample market prices
│
├── requirements.txt          # Python dependencies
├── README.txt               # This file
│
├── templates/               # HTML pages
│   ├── login.html           # Login page
│   ├── register.html        # User registration
│   ├── dashboard.html       # User dashboard
│   ├── profile.html         # User profile page
│   ├── crop.html            # Crop advisor page
│   ├── market.html          # Market prices page
│   ├── schemes.html         # Government schemes
│   ├── feedback.html        # Feedback form
│   ├── admin_dashboard.html # Admin panel
│   ├── admin_market.html    # Admin market management
│   └── ... (other pages)
│
├── static/                  # Static files
│   ├── data/
│   │   └── india_districts.json  # State and district data
│   ├── image/              # Image files
│   └── js/
│       └── market.js       # JavaScript for market page

========================================
🤖 TECHNOLOGY STACK
========================================

- Language: Python 3
- Framework: Flask (web framework)
- Database: SQLite
- Frontend: HTML, CSS, Bootstrap 5
- Icons: Font Awesome
- Styling: Bootstrap Utilities

========================================
📱 USER ROLES
========================================

1. REGULAR USER
   - Register and login
   - Update profile information
   - Get crop recommendations
   - View market prices
   - Browse government schemes
   - Submit feedback
   - Logout

2. ADMIN
   - Login to admin panel
   - View all users
   - Update market prices
   - View user feedbacks
   - Monitor user activities
   - Manage system settings

========================================
🔐 SECURITY FEATURES
========================================

- Password hashing for security
- Session management
- User authentication required
- Admin-only access to sensitive pages
- OTP verification (planned feature)

========================================
📝 MAIN FILES EXPLAINED
========================================

app.py
  - Contains all routes and pages
  - Handles user login/registration
  - Manages requests from frontend

db.py
  - Creates database tables
  - Manages database connection
  - Sets up admin user

config.py
  - Application settings
  - Language translations
  - Configuration variables

crop_logic.py
  - Crop recommendation algorithm
  - Filters crops based on criteria

utils.py
  - Helper functions
  - Common utilities

========================================
🌐 MULTI-LANGUAGE SUPPORT
========================================

The app supports 3 languages:
- English
- Marathi (मराठी)
- Hindi (हिंदी)

Users can switch languages using language selector in navbar.

========================================
📊 DATABASE TABLES
========================================

- users: User profiles and information
- admins: Admin credentials
- crops: Crop data and recommendations
- schemes: Government schemes information
- feedback: User feedback submissions
- market_prices: Current market prices
- user_activity: User actions log
- farmer_types: Types of farmers

========================================
❗ TROUBLESHOOTING
========================================

ISSUE: "Unable to connect to database"
SOLUTION: Run setup_database.py first

ISSUE: "Port 5000 already in use"
SOLUTION: Change port in app.py or stop other app using port 5000

ISSUE: "Module not found"
SOLUTION: Run: pip install -r requirements.txt

ISSUE: "Page not loading"
SOLUTION: Clear browser cache and reload

========================================
🚀 FEATURES COMING SOON
========================================

- Weather-based recommendations
- SMS/Email notifications
- Mobile app version
- Real-time price updates
- Video tutorials
- Farmer community forum

========================================
📞 SUPPORT
========================================

For issues or suggestions, please contact the development team.

========================================
📄 LICENSE & CREDITS
========================================

Project FA - Farmer Assistant Application
Version 1.0
Built with Python and Flask

========================================