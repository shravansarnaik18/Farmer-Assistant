"""Database initialization and operations for Farmer Assistant app."""

import sqlite3
from contextlib import contextmanager
from functools import lru_cache

DB_PATH = "database.db"

# Connection pool for better performance
_db_conn = None


def get_db_connection():
    """Get or create database connection."""
    global _db_conn
    if _db_conn is None:
        _db_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _db_conn.row_factory = sqlite3.Row
        # Enable query optimization
        _db_conn.execute("PRAGMA query_only = OFF")
        _db_conn.execute("PRAGMA journal_mode = WAL")
    return _db_conn


@contextmanager
def db_connection():
    """Context manager for database operations."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def init_database():
    """Initialize database tables with indexes."""
    conn = get_db_connection()
    
    # Users table with farmer profile fields
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            mobile TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            age INTEGER,
            farmer_type TEXT,
            state TEXT,
            district TEXT,
            village TEXT,
            land_hectares REAL,
            experience_years INTEGER,
            primary_crop TEXT,
            irrigation_type TEXT,
            soil_type TEXT,
            farming_method TEXT
        )
    ''')

    # Crops table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS crops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_name TEXT NOT NULL,
            season TEXT NOT NULL,
            soil_type TEXT NOT NULL,
            fertilizer TEXT,
            pest_control TEXT,
            UNIQUE(crop_name)  -- ensure each crop appears only once
        )
    ''')

    # Schemes table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS schemes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            link TEXT
        )
    ''')

    # Market prices table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS market_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_name TEXT NOT NULL,
            price REAL,
            date DATE NOT NULL
        )
    ''')

    # User activity log table (simplified for performance)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # Admin users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')


    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    #farmers table for community insights
    # Create table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS farmer_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    ''')

    # Insert data only if table is empty (prevents duplicates on app restart)
    existing_count = conn.execute("SELECT COUNT(*) FROM farmer_types").fetchone()[0]
    if existing_count == 0:
        conn.executemany('''
        INSERT INTO farmer_types (name) VALUES (?)
        ''', [
            ('Small Farmer',),
            ('Medium Farmer',),
            ('Large Farmer',),
            ('Marginal Farmer',)
        ])

    # automatically add a default admin if none exists
    from werkzeug.security import generate_password_hash
    try:
        existing = conn.execute("SELECT 1 FROM admins LIMIT 1").fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO admins (username, password) VALUES (?,?)",
                ("admin", generate_password_hash("admin"))
            )
    except Exception:
        # ignore errors during default creation, table may not exist yet
        pass


    # Create indexes for faster queries
    try:
        conn.execute('CREATE INDEX IF NOT EXISTS idx_users_mobile ON users(mobile)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_users_state_district ON users(state, district)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_users_farmer_type ON users(farmer_type)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_crops_season_soil ON crops(season, soil_type)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_activity_user ON user_activity(user_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON user_activity(timestamp DESC)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_market_crop_date ON market_prices(crop_name, date DESC)')
        # index for admin username lookups
        conn.execute('CREATE INDEX IF NOT EXISTS idx_admin_username ON admins(username)')
    except sqlite3.OperationalError:
        pass  # Indexes may already exist

    conn.commit()
    
    # Populate crops if empty
    populate_crops_data()


# ============================================================================
# CROP DATA POPULATION
# ============================================================================

def populate_crops_data():
    """Populate database with comprehensive crop varieties.
    Also clean up duplicates and ensure full list is present. This function now
    uses `INSERT OR IGNORE` and removes any duplicate entries so the dropdown
    on the market page always reflects the complete set of crops.
    """
    crops_data = [
        # Cereals - Rabi (Winter)
        ('Wheat', 'Rabi', 'Clay loam, Loam', 'DAP, Urea', 'Armyworm, Aphids'),
        ('Barley', 'Rabi', 'Loam, Sandy loam', 'Urea, DAP', 'Armyworm'),
        ('Gram (Chickpea)', 'Rabi', 'Clay loam, Well-drained', 'DAP, Potash', 'Pod borer'),
        ('Peas', 'Rabi', 'Loam, Sandy loam', 'DAP, Urea', 'Armyworm'),
        
        # Cereals - Kharif (Summer)
        ('Rice', 'Kharif', 'Alluvial, Clay loam', 'Urea, DAP', 'Stem borer, Brown planthopper'),
        ('Maize', 'Kharif', 'Well-drained loam', 'Urea, DAP', 'Stem borer, Armyworm'),
        ('Jowar', 'Kharif', 'Red soil, Loam', 'Urea, DAP', 'Shoot fly'),
        ('Cotton', 'Kharif', 'Black soil, Loam', 'NPK, Potash', 'Bollworm, Leafworm'),
        
        # Pulses
        ('Moong', 'Kharif', 'Sandy loam, Loam', 'DAP', 'Thrips, Leaf roller'),
        ('Masoor', 'Rabi', 'Well-drained loam', 'DAP, Urea', 'Stem fly, Gram pod borer'),
        ('Arhar', 'Kharif', 'Black soil, Red soil', 'DAP, Potash', 'Pod borer'),
        ('Urad', 'Kharif', 'Loam, Sandy loam', 'DAP', 'Leaf roller, Thrips'),
        
        # Oilseeds
        ('Groundnut', 'Kharif', 'Light sandy loam', 'DAP, Phosphorus', 'Leaf miner, Jassids'),
        ('Soybean', 'Kharif', 'Black soil, Loam', 'DAP, Potash', 'Yellow mosaic virus'),
        ('Sunflower', 'Kharif', 'Well-drained loam', 'Urea, DAP', 'Stem weevil'),
        ('Rapeseed', 'Rabi', 'Loam, Clay loam', 'Urea, DAP', 'Saw fly, Leaf roller'),
        
        # Spices
        ('Chilli', 'Kharif', 'Well-drained loam', 'NPK, Potash', 'Thrips, Fruit rot'),
        ('Turmeric', 'Kharif', 'Well-drained loam', 'Compost, Potash', 'Leaf blotch, Storage rot'),
        ('Cumin', 'Rabi', 'Sandy loam, Well-drained', 'DAP, Potash', 'Aphids'),
        ('Coriander', 'Rabi', 'Loam, Sandy loam', 'Urea, DAP', 'Aphids, Armyworm'),
        
        # Vegetables
        ('Tomato', 'Kharif', 'Well-drained loam', 'NPK, Compost', 'Fruit borer, Early blight'),
        ('Onion', 'Rabi', 'Loam, Sandy loam', 'Urea, DAP', 'Thrips, Purple blotch'),
        ('Potato', 'Rabi', 'Loam, Sandy loam', 'Urea, DAP', 'Late blight, Leafminer'),
        ('Cabbage', 'Rabi', 'Loam, Clay loam', 'Urea, DAP', 'Cabbage butterfly, Leaf blight'),
        ('Carrot', 'Rabi', 'Loam, Sandy loam', 'Urea, Potash', 'Root knot nematode'),
        ('Cucumber', 'Kharif', 'Sandy loam, Well-drained', 'NPK, Compost', 'Downy mildew, Fruit fly'),
        
        # Fruits
        ('Sugarcane', 'Annual', 'Clay loam, Alluvial', 'Urea, DAP, Potash', 'Top borer, Scale insect'),
        ('Mango', 'Year-round', 'Well-drained loam', 'NPK, Compost', 'Anthracnose, Leaf spot'),
        ('Banana', 'Year-round', 'Well-drained loam', 'Potash, Compost', 'Leaf spot, Panama wilt'),
        ('Coconut', 'Year-round', 'Sandy loam, Loam', 'Potash, Phosphorus', 'Rhinoceros beetle'),
    ]
    
    with db_connection() as conn:
        # remove any accidental duplicates first (keep lowest id for each name)
        conn.execute("""
            DELETE FROM crops
            WHERE id NOT IN (
                SELECT MIN(id) FROM crops GROUP BY crop_name
            )
        """)
        # insert all listed crops, skip if crop_name already exists
        for crop in crops_data:
            conn.execute(
                """
                INSERT INTO crops (crop_name, season, soil_type, fertilizer, pest_control)
                SELECT ?,?,?,?,?
                WHERE NOT EXISTS (SELECT 1 FROM crops WHERE crop_name = ?)
                """,
                (crop[0], crop[1], crop[2], crop[3], crop[4], crop[0])
            )
        conn.commit()


# ============================================================================
# OPTIMIZED DATABASE QUERIES
# ============================================================================

def get_user_by_mobile(mobile):
    """Get user by mobile number - O(log n) with index."""
    with db_connection() as conn:
        return conn.execute(
            "SELECT id, name, password FROM users WHERE mobile = ?",
            (mobile,)
        ).fetchone()


def get_user_by_id(user_id):
    """Get user by ID - O(1) primary key lookup."""
    with db_connection() as conn:
        return conn.execute(
            "SELECT id, name, mobile, age, farmer_type, state, district, village, land_hectares, experience_years, primary_crop, irrigation_type, soil_type, farming_method FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()


def user_exists(mobile):
    """Check if user exists - faster than get_user (COUNT instead of *)."""
    with db_connection() as conn:
        result = conn.execute(
            "SELECT 1 FROM users WHERE mobile = ? LIMIT 1",
            (mobile,)
        ).fetchone()
        return result is not None


def create_user(name, mobile, password_hash):
    """Create a new user - single operation."""
    try:
        with db_connection() as conn:
            conn.execute(
                "INSERT INTO users (name, mobile, password) VALUES (?,?,?)",
                (name, mobile, password_hash),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def update_user(user_id, name, mobile, age=None, farmer_type=None, state=None, district=None, village=None, land_hectares=None, experience_years=None, primary_crop=None, irrigation_type=None, soil_type=None, farming_method=None):
    """Update user information."""
    try:
        with db_connection() as conn:
            conn.execute(
                """UPDATE users SET 
                    name = ?, mobile = ?, age = ?, farmer_type = ?, state = ?, district = ?, village = ?, 
                    land_hectares = ?, experience_years = ?, primary_crop = ?, irrigation_type = ?, 
                    soil_type = ?, farming_method = ? 
                WHERE id = ?""",
                (name, mobile, age, farmer_type, state, district, village, land_hectares, experience_years, primary_crop, irrigation_type, soil_type, farming_method, user_id)
            )
        return True
    except sqlite3.IntegrityError:
        return False


def update_password(mobile, password_hash):
    """Update user password."""
    with db_connection() as conn:
        conn.execute(
            "UPDATE users SET password = ? WHERE mobile = ?",
            (password_hash, mobile)
        )


def delete_user(user_id):
    """Delete user and their activity logs - batch operation."""
    with db_connection() as conn:
        # Single batch delete is faster than two separate deletes
        conn.execute("DELETE FROM user_activity WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))


def log_activity(user_id, action):
    """Log user activity - async-friendly (no immediate wait)."""
    try:
        with db_connection() as conn:
            conn.execute(
                "INSERT INTO user_activity (user_id, action) VALUES (?,?)",
                (user_id, action)
            )
    except Exception:
        pass  # Don't block on activity logging


def get_user_activities(user_id, limit=20):
    """Get user activity log - O(log n) with timestamp index."""
    with db_connection() as conn:
        return conn.execute(
            "SELECT action, timestamp FROM user_activity WHERE user_id=? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()


def get_personalized_crop_recommendations(user_id):
    """Get crop recommendations based on farmer profile."""
    user = get_user_by_id(user_id)
    if not user:
        return []
    
    with db_connection() as conn:
        # Base query for crops
        query = "SELECT * FROM crops WHERE 1=1"
        params = []
        
        # Filter by user's soil type if available
        if user['soil_type']:
            query += " AND soil_type LIKE ?"
            params.append(f"%{user['soil_type']}%")
        
        # Filter by season based on current month (simplified logic)
        import datetime
        current_month = datetime.datetime.now().month
        if current_month in [10, 11, 12, 1, 2, 3]:  # Rabi season
            query += " AND season = ?"
            params.append("Rabi")
        elif current_month in [6, 7, 8, 9]:  # Kharif season
            query += " AND season = ?"
            params.append("Kharif")
        
        # Order by relevance (soil match first, then general)
        crops = conn.execute(query, params).fetchall()
        
        # If no specific matches, return general recommendations
        if not crops:
            crops = conn.execute("SELECT * FROM crops LIMIT 10").fetchall()
        
        return crops


# ---------------------------------------------------------------------------
# Admin helpers
# ---------------------------------------------------------------------------

def create_admin(username, password_hash):
    """Create a new admin user."""
    try:
        with db_connection() as conn:
            conn.execute(
                "INSERT INTO admins (username, password) VALUES (?,?)",
                (username, password_hash)
            )
        return True
    except sqlite3.IntegrityError:
        return False


def get_admin_by_username(username):
    """Retrieve admin record by username."""
    with db_connection() as conn:
        return conn.execute(
            "SELECT id, username, password FROM admins WHERE username = ?",
            (username,)
        ).fetchone()


def get_all_users(limit=100):
    """Return a list of regular users for admin dashboard."""
    with db_connection() as conn:
        return conn.execute(
            "SELECT id, name, mobile, state, district, primary_crop FROM users ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()


def get_nearby_farmers(user_id, limit=5):
    """Get farmers from same district for community insights."""
    user = get_user_by_id(user_id)
    if not user or not user['district']:
        return []
    
    with db_connection() as conn:
        return conn.execute(
            "SELECT name, village, primary_crop, land_hectares FROM users WHERE district = ? AND id != ? AND primary_crop IS NOT NULL LIMIT ?",
            (user['district'], user_id, limit)
        ).fetchall()


def get_crops_by_criteria(season, soil_type):
    """Get crops - O(log n) with composite index."""
    with db_connection() as conn:
        return conn.execute(
            "SELECT * FROM crops WHERE season = ? AND soil_type = ?",
            (season, soil_type)
        ).fetchall()


@lru_cache(maxsize=1)
def get_all_schemes():
    """Get all schemes - cached in memory (rarely changes)."""
    with db_connection() as conn:
        return tuple(conn.execute("SELECT * FROM schemes").fetchall())


def clear_schemes_cache():
    """Clear schemes cache when schemes are updated."""
    get_all_schemes.cache_clear()


# ============================================================================
# MARKET PRICE FUNCTIONS
# ============================================================================

def get_all_crops():
    """Get all available crops for market tracking."""
    with db_connection() as conn:
        return conn.execute(
            "SELECT DISTINCT crop_name FROM crops ORDER BY crop_name"
        ).fetchall()


def get_crop_by_name(crop_name):
    """Get crop details by name including fertilizer and pest control."""
    with db_connection() as conn:
        return conn.execute(
            "SELECT id, crop_name, season, soil_type, fertilizer, pest_control FROM crops WHERE crop_name = ? LIMIT 1",
            (crop_name,)
        ).fetchone()


def get_market_price(crop_name, days=30):
    """Get market price history for a crop."""
    with db_connection() as conn:
        return conn.execute(
            """SELECT crop_name, price, date FROM market_prices 
               WHERE crop_name = ? 
               ORDER BY date DESC LIMIT ?""",
            (crop_name, days)
        ).fetchall()


def add_market_price(crop_name, price, date=None):
    """Add a new market price entry."""
    if date is None:
        import datetime
        date = datetime.date.today()
    
    try:
        with db_connection() as conn:
            conn.execute(
                "INSERT INTO market_prices (crop_name, price, date) VALUES (?,?,?)",
                (crop_name, price, date)
            )
        return True
    except Exception:
        return False


def update_market_prices(prices_dict):
    """Update multiple market prices at once.
    Expected format: {'crop_name': price, 'crop_name2': price2, ...}
    """
    import datetime
    today = datetime.date.today()
    
    try:
        with db_connection() as conn:
            for crop_name, price in prices_dict.items():
                conn.execute(
                    "INSERT INTO market_prices (crop_name, price, date) VALUES (?,?,?)",
                    (crop_name, price, today)
                )
        return True
    except Exception:
        return False


def get_price_trend(crop_name, days=7):
    """Get price trend data for analysis."""
    prices = get_market_price(crop_name, days)
    if not prices:
        return None
    
    prices_list = [p[1] for p in reversed(prices)]
    
    if len(prices_list) < 2:
        return None
    
    # Calculate trend
    start_price = prices_list[0]
    end_price = prices_list[-1]
    change = end_price - start_price
    change_percent = (change / start_price * 100) if start_price != 0 else 0
    
    # Calculate average
    avg_price = sum(prices_list) / len(prices_list)
    
    return {
        'current_price': end_price,
        'previous_price': start_price,
        'change': change,
        'change_percent': round(change_percent, 2),
        'trend': 'Upward' if change > 0 else 'Downward' if change < 0 else 'Stable',
        'avg_price': round(avg_price, 2),
        'max_price': max(prices_list),
        'min_price': min(prices_list)
    }



# ============================================================================
# ACTIVITY & LOGIN HISTORY FUNCTIONS (ADMIN FEATURES)
# ============================================================================

def get_all_activity_history(limit=100):
    """Get all user activity logs with user details for admin dashboard."""
    with db_connection() as conn:
        return conn.execute(
            """SELECT ua.id, u.name, u.mobile, ua.action, ua.timestamp 
               FROM user_activity ua
               JOIN users u ON ua.user_id = u.id
               ORDER BY ua.timestamp DESC 
               LIMIT ?""",
            (limit,)
        ).fetchall()


def get_login_history(limit=50):
    """Get login/logout history for all users."""
    with db_connection() as conn:
        return conn.execute(
            """SELECT ua.id, u.id as user_id, u.name, u.mobile, ua.action, ua.timestamp 
               FROM user_activity ua
               JOIN users u ON ua.user_id = u.id
               WHERE ua.action IN ('login', 'logout')
               ORDER BY ua.timestamp DESC 
               LIMIT ?""",
            (limit,)
        ).fetchall()


def get_user_login_history(user_id, limit=20):
    """Get login history for a specific user."""
    with db_connection() as conn:
        return conn.execute(
            """SELECT action, timestamp 
               FROM user_activity 
               WHERE user_id = ? AND action IN ('login', 'logout')
               ORDER BY timestamp DESC 
               LIMIT ?""",
            (user_id, limit)
        ).fetchall()


def get_activity_stats():
    """Get activity statistics for admin dashboard."""
    with db_connection() as conn:
        # Total logins today
        today_logins = conn.execute(
            """SELECT COUNT(*) FROM user_activity 
               WHERE action = 'login' 
               AND DATE(timestamp) = DATE('now')"""
        ).fetchone()[0]
        
        # Total unique users today
        today_active_users = conn.execute(
            """SELECT COUNT(DISTINCT user_id) FROM user_activity 
               WHERE DATE(timestamp) = DATE('now')"""
        ).fetchone()[0]
        
        # Most active user
        most_active = conn.execute(
            """SELECT u.name, u.mobile, COUNT(*) as activity_count 
               FROM user_activity ua
               JOIN users u ON ua.user_id = u.id
               GROUP BY ua.user_id
               ORDER BY activity_count DESC
               LIMIT 1"""
        ).fetchone()
        
        return {
            'today_logins': today_logins,
            'today_active_users': today_active_users,
            'most_active_user': dict(most_active) if most_active else None
        }


def close_db():
    """Close database connection on app shutdown."""
    global _db_conn
    if _db_conn:
        _db_conn.close()
        _db_conn = None
