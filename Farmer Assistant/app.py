"""
Farmer Assistant - Optimized for Performance

Reduced complexity, better time management, and efficient database operations.
"""

import os
import requests
import random
import datetime
from flask import Flask, render_template, request, redirect, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from functools import wraps
from apscheduler.schedulers.background import BackgroundScheduler

# Import optimized modules
try:
    from config import get_text, SUPPORTED_LANGS
    from db import (
        init_database, close_db,
        get_user_by_mobile, get_user_by_id, user_exists,
        create_user, update_user, update_password, delete_user, 
        log_activity, get_user_activities, get_crops_by_criteria, 
        get_all_schemes, get_nearby_farmers, get_personalized_crop_recommendations,
        create_admin, get_admin_by_username, get_all_users,
        get_all_crops, get_market_price, add_market_price, update_market_prices, get_price_trend,
        get_crop_by_name, get_all_activity_history, get_login_history, get_user_login_history, get_activity_stats
    )
    from utils import generate_otp, send_otp_sms
    from crop_logic import get_crop_suggestions
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure db_optimized.py, config.py, utils.py, and crop_logic.py are in the same directory as app.py")
    raise

load_dotenv()

# Initialize Flask
app = Flask(__name__)
app.secret_key = "supersecretkey1234"

# Add cache control headers to prevent browser caching
@app.after_request
def set_cache_control(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Initialize database
init_database()

# Ensure at least one admin exists (safeguard when setup script is skipped)
from werkzeug.security import generate_password_hash
from db import db_connection, get_admin_by_username, create_admin, get_db_connection
if not get_admin_by_username("admin"):
    # default credentials are "admin" / "admin"
    create_admin("admin", generate_password_hash("admin"))


# ============================================================================
# MARKET PRICE AUTO-UPDATE SCHEDULER
# ============================================================================

def update_market_prices_auto():
    """Background task to update market prices with simulated data."""
    try:
        from db import get_all_crops, update_market_prices
        crops = get_all_crops()
        prices_dict = {}
        
        for crop in crops:
            crop_name = crop[0]
            # Simulate realistic price variations (±10%)
            base_prices = {
                'Wheat': 2200, 'Rice': 2800, 'Maize': 1800, 'Cotton': 5500,
                'Groundnut': 4500, 'Soybean': 3500, 'Sunflower': 3800,
                'Onion': 1500, 'Potato': 1000, 'Tomato': 1200,
                'Chilli': 3500, 'Gram': 4500, 'Moong': 4800, 'Arhar': 5000
            }
            base_price = base_prices.get(crop_name, 2500)
            variation = random.uniform(0.9, 1.1)  # ±10% variation
            current_price = round(base_price * variation, 2)
            prices_dict[crop_name] = current_price
        
        update_market_prices(prices_dict)
        print(f"[{datetime.datetime.now()}] Market prices updated: {len(prices_dict)} crops")
    except Exception as e:
        print(f"Error updating market prices: {str(e)}")


# Initialize scheduler for market prices
scheduler = BackgroundScheduler()
# Daily market price updates at key trading times
scheduler.add_job(func=update_market_prices_auto, trigger="cron", hour=6, minute=0, id='daily_morning_update')      # 6 AM
scheduler.add_job(func=update_market_prices_auto, trigger="cron", hour=12, minute=0, id='daily_noon_update')        # 12 PM
scheduler.add_job(func=update_market_prices_auto, trigger="cron", hour=16, minute=0, id='daily_afternoon_update')   # 4 PM
scheduler.add_job(func=update_market_prices_auto, trigger="cron", hour=20, minute=0, id='daily_evening_update')     # 8 PM

# Only start scheduler if not in debug mode with reloader
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not os.getenv("DEBUG", "False").lower() == "true":
    if not scheduler.running:
        scheduler.start()
        print("Market price auto-update scheduler started - Daily updates at 6 AM, 12 PM, 4 PM, 8 PM")

# Cleanup on exit
@app.teardown_appcontext
def shutdown_db(exception=None):
    """Close database connection on app shutdown."""
    close_db()


# ============================================================================
# DECORATORS & HELPERS
# ============================================================================

def login_required(f):
    """Require user to be logged in (farmer)."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash(get_text(get_lang()).get("login_required"), "error")
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    """Require admin login for protected routes."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            text = get_text(get_lang())
            msg = text.get("admin_login_required") or "Administrator login required"
            flash(msg, "error")
            return redirect("/admin/login")
        return f(*args, **kwargs)
    return wrapper


def get_lang():
    """Get language from session - O(1) dict lookup."""
    lang = session.get("lang", "en")
    # Validate language exists, fallback to 'en'
    return lang if lang in SUPPORTED_LANGS else "en"


def render(template, **kwargs):
    """Helper to simplify rendering with translations and user info."""
    kwargs.setdefault("text", get_text(get_lang()))
    kwargs.setdefault("user_name", session.get("user_name"))
    return render_template(template, **kwargs)


def handle_otp_form(step, pending_key, success_redirect, success_msg, error_template_args):
    """
    Consolidate OTP verification logic.
    Reduces code duplication between register and forgot flows.
    """
    pending = session.get(pending_key)
    if not pending:
        flash(get_text(get_lang()).get("otp_incorrect"), "error")
        return redirect(error_template_args.get("error_redirect", "/"))

    otp = request.form.get("otp", "").strip()
    if otp != pending.get("otp"):
        flash(get_text(get_lang()).get("otp_incorrect"), "error")
        return render(error_template_args["template"], **error_template_args.get("context", {}))

    # OTP verified - execute step callback
    result = step(pending)
    if result is True:
        session.pop(pending_key, None)
        flash(get_text(get_lang()).get(success_msg), "success")
        return redirect(success_redirect)
    elif isinstance(result, str):
        # Return error message
        flash(result, "error")
    
    return render(error_template_args["template"], **error_template_args.get("context", {}))


@app.context_processor
def inject_globals():
    """Make translations and common session flags available globally."""
    return {
        "text": get_text(get_lang()),
        "user_name": session.get("user_name"),
        "lang": get_lang(),
        "admin_logged_in": session.get("admin_logged_in"),
        "admin_username": session.get("admin_username")
    }


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route("/")
def home():
    """Home page."""
    if "user_id" in session:
        return redirect("/dashboard")
    return render("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register with OTP verification."""
    text = get_text(get_lang())

    # Handle OTP verification
    if request.method == "POST" and request.form.get("otp"):
        def create_account(pending):
            if create_user(pending["name"], pending["mobile"], pending["password"]):
                return True
            return text.get("mobile_exists")
        
        return handle_otp_form(
            create_account,
            "pending_registration",
            "/login",
            "registration_success",
            {
                "template": "otp_verify.html",
                "error_redirect": "/register",
                "context": {
                    "title": text.get("otp_title_reg"),
                    "message": text.get("otp_reg_msg"),
                    "action": "/register",
                    "password_field": False
                }
            }
        )

    # Handle initial registration
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        mobile = request.form.get("mobile", "").strip()
        password = request.form.get("password", "").strip()

        # Basic field presence
        if not all([name, mobile, password]):
            flash(text.get("all_fields_required"), "error")
            return render("register.html")

        # Format validation
        if not mobile.isdigit() or len(mobile) != 10:
            flash(text.get("mobile_invalid", "Mobile number must be exactly 10 digits"), "error")
            return render("register.html")
        if len(password) < 6:
            flash(text.get("password_invalid", "Password must be at least 6 characters"), "error")
            return render("register.html")

        if user_exists(mobile):  # Faster than get_user_by_mobile
            flash(text.get("mobile_exists"), "error")
            return render("register.html")

        # Send OTP and store pending data
        otp = generate_otp()
        session["pending_registration"] = {
            "name": name,
            "mobile": mobile,
            "password": generate_password_hash(password),
            "otp": otp,
        }
        send_otp_sms(mobile, otp)
        flash(text.get("otp_sent"), "success")
        return render("otp_verify.html",
                     title=text.get("otp_title_reg"),
                     message=text.get("otp_reg_msg"),
                     action="/register",
                     password_field=False)

    return render("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login with mobile and password."""
    text = get_text(get_lang())

    if request.method == "POST":
        mobile = request.form.get("mobile", "").strip()
        password = request.form.get("password", "").strip()

        # basic format checks
        if not mobile.isdigit() or len(mobile) != 10:
            flash(text.get("mobile_invalid", "Mobile number must be exactly 10 digits"), "error")
            return render("login.html")
        if len(password) < 6:
            flash(text.get("password_invalid", "Password must be at least 6 characters"), "error")
            return render("login.html")

        user = get_user_by_mobile(mobile)
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            log_activity(user["id"], "login")
            return redirect("/dashboard")
        
        flash(text.get("invalid_credentials"), "error")

    return render("login.html")


@app.route("/forgot", methods=["GET", "POST"])
def forgot_password():
    """Reset password with OTP verification."""
    text = get_text(get_lang())

    # Handle OTP verification
    if request.method == "POST" and request.form.get("otp"):
        def reset_password(pending):
            new_pass = request.form.get("password", "").strip()
            if not new_pass:
                return "Password required"
            if len(new_pass) < 6:
                return text.get("password_invalid", "Password must be at least 6 characters")
            update_password(pending["mobile"], generate_password_hash(new_pass))
            return True
        
        return handle_otp_form(
            reset_password,
            "pending_reset",
            "/login",
            "password_reset_success",
            {
                "template": "otp_verify.html",
                "error_redirect": "/forgot",
                "context": {
                    "title": text.get("otp_title_forgot"),
                    "message": text.get("otp_forgot_msg"),
                    "action": "/forgot",
                    "password_field": True
                }
            }
        )

    # Handle initial forgot request
    if request.method == "POST":
        mobile = request.form.get("mobile", "").strip()
        if not mobile.isdigit() or len(mobile) != 10:
            flash(text.get("mobile_invalid", "Mobile number must be exactly 10 digits"), "error")
            return render("forgot.html")
        if not user_exists(mobile):
            flash(text.get("user_not_found"), "error")
            return render("forgot.html")

        otp = generate_otp()
        session["pending_reset"] = {"mobile": mobile, "otp": otp}
        send_otp_sms(mobile, otp)
        flash(text.get("otp_sent"), "success")
        return render("otp_verify.html",
                     title=text.get("otp_title_forgot"),
                     message=text.get("otp_forgot_msg"),
                     action="/forgot",
                     password_field=True)

    return render("forgot.html")


@app.route("/logout")
def logout():
    """Logout user."""
    if "user_id" in session:
        log_activity(session["user_id"], "logout")
    session.clear()
    return redirect("/")


# ------------------ Admin Authentication ------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Administrator login page with translation support."""
    text = get_text(get_lang())
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        admin = get_admin_by_username(username)
        if admin and check_password_hash(admin["password"], password):
            session["admin_logged_in"] = True
            session["is_admin"] = True
            session["admin_username"] = username
            return redirect("/admin/dashboard")
        flash(text.get("invalid_credentials"), "error")
    # use render helper to provide translations and session context
    return render("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)
    # after logging out, send admin back to their login page
    return redirect("/admin/login")


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    """Simple admin dashboard showing registered users."""
    users = get_all_users()
    stats = get_activity_stats()
    # use helper to ensure translations/context available
    return render("admin_dashboard.html", users=users, stats=stats)


@app.route("/admin/activity_history")
@admin_required
def admin_activity_history():
    """Admin view of all user activities."""
    text = get_text(get_lang())
    activities = get_all_activity_history(limit=200)
    activities = [dict(a) for a in activities] if activities else []
    return render("admin_activity_history.html", activities=activities, text=text)


@app.route("/admin/login_history")
@admin_required
def admin_login_history():
    """Admin view of login/logout history."""
    text = get_text(get_lang())
    login_history = get_login_history(limit=100)
    login_history = [dict(h) for h in login_history] if login_history else []
    return render("admin_login_history.html", login_history=login_history, text=text)



# ============================================================================
# MAIN FEATURES
# ============================================================================

@app.route("/dashboard")
@login_required
def dashboard():
    """User dashboard."""
    log_activity(session["user_id"], "viewed dashboard")
    return render("dashboard.html")

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """User profile."""
    try:
        user = get_user_by_id(session["user_id"])
        text = get_text(get_lang())

        if user:
            user = dict(user)
        else:
            session.clear()
            flash(text.get("login_required"), "error")
            return redirect("/login")

        # GET farmer types from DB (unique only)
        conn = get_db_connection()
        farmer_types = conn.execute(
            "SELECT DISTINCT name FROM farmer_types ORDER BY name"
        ).fetchall()
        farmer_types = [dict(ft) for ft in farmer_types]

        # ---------------- POST ----------------
        if request.method == "POST":

            def to_int(val):
                try:
                    return int(val)
                except:
                    return None

            def to_float(val):
                try:
                    return float(val)
                except:
                    return None

            new_name = request.form.get("name", user["name"]).strip()
            new_mobile = request.form.get("mobile", user["mobile"]).strip()

            age = to_int(request.form.get("age"))
            land_hectares = to_float(request.form.get("land_hectares"))
            experience_years = to_int(request.form.get("experience_years"))

            farmer_type = request.form.get("farmer_type") or None
            state = request.form.get("state") or None
            district = request.form.get("district") or None
            village = request.form.get("village") or None

            primary_crop = request.form.get("primary_crop") or None
            irrigation_type = request.form.get("irrigation_type") or None
            soil_type = request.form.get("soil_type") or None
            farming_method = request.form.get("farming_method") or None

            # 🔥 Validation
            if not new_name or not new_mobile:
                flash(text.get("name_mobile_required"), "error")

            elif new_mobile != user["mobile"] and user_exists(new_mobile):
                flash(text.get("mobile_exists"), "error")

            else:
                update_user(
                    session["user_id"],
                    new_name,
                    new_mobile,
                    age,
                    farmer_type,
                    state,
                    district,
                    village,
                    land_hectares,
                    experience_years,
                    primary_crop,
                    irrigation_type,
                    soil_type,
                    farming_method
                )

                session["user_name"] = new_name
                log_activity(session["user_id"], "updated profile")
                flash(text.get("update_success"), "success")

                # Reload user
                user = get_user_by_id(session["user_id"])
                user = dict(user) if user else user

        # ---------------- EXTRA DATA ----------------
        activities = get_user_activities(session["user_id"])
        activities = [dict(a) for a in activities] if activities else []

        nearby_farmers = get_nearby_farmers(session["user_id"])
        nearby_farmers = [dict(f) for f in nearby_farmers] if nearby_farmers else []

        personalized_crops = get_personalized_crop_recommendations(session["user_id"])
        personalized_crops = [dict(c) for c in personalized_crops] if personalized_crops else []

        conn.close()

        return render(
            "profile.html",
            user=user,
            text=text,
            farmer_types=farmer_types,   # 🔥 IMPORTANT
            activities=activities,
            nearby_farmers=nearby_farmers,
            personalized_crops=personalized_crops
        )

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return render("error.html", error="Unable to render profile."), 500

@app.route("/delete_account", methods=["POST"])
@login_required
def delete_account():
    """Delete account."""
    user_id = session["user_id"]
    delete_user(user_id)
    session.clear()
    flash(get_text("en").get("account_deleted"), "success")
    return redirect("/")


@app.route("/crop", methods=["GET", "POST"])
@login_required
def crop_advisory():
    
    try:
        text = get_text(get_lang())
        crops = None
        user_id = session.get("user_id")

        if not user_id:
            return redirect("/login")

        user = get_user_by_id(user_id)

        if user:
            user = dict(user)

        # Define seasons and soil types for the form
        seasons = ["Kharif", "Rabi", "Zaid"]
        soils = ["Black Soil", "Loamy Soil", "Clay Soil"]

        if request.method == "POST":
            season = request.form.get("season", "").strip()
            soil = request.form.get("soil", "").strip()

            if season and soil:
                print(f"✅ POST received: season='{season}', soil='{soil}'")

                # 🔹 FIRST try DB
                crops = get_crops_by_criteria(season, soil)
                print(f"✅ DB query returned: {crops}")

                # 🔹 IF DB EMPTY → use logic fallback
                if not crops:
                    crop_list = get_crop_suggestions(season, soil)
                    print(f"✅ get_crop_suggestions returned: {crop_list}")

                    if crop_list:
                        crops = []
                        for crop_name in crop_list:
                            crop_detail = get_crop_by_name(crop_name)
                            if crop_detail:
                                crops.append(dict(crop_detail))
                            else:
                                # Fallback if crop not found in DB
                                crops.append({
                                    "crop_name": crop_name,
                                    "fertilizer": "NPK",
                                    "pest_control": "Basic spray",
                                    "season": season,
                                    "soil_type": soil
                                })
                        print(f"✅ Built crops list with details: {crops}")
                    else:
                        print(f"⚠️ get_crop_suggestions returned empty list!")
                        crops = []
                else:
                    crops = [dict(c) for c in crops]
                    print(f"✅ Using DB crops: {crops}")

                log_activity(user_id, f"searched {season}/{soil}")

        else:
            if user and (user.get("soil_type") or user.get("state") or user.get("primary_crop")):
                crops = get_personalized_crop_recommendations(user_id)

                if crops:
                    crops = [dict(c) for c in crops]
        
        print(f"DEBUG: Final crops to render: {crops}")
        return render("crop.html", crops=crops, user=user, seasons=seasons, soils=soils, text=text)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        flash(text.get("crop_page_error"), "error")
        return redirect("/dashboard")
    
# Feedback route
@app.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():
    text = get_text(get_lang())

    if request.method == "POST":
        message = request.form.get("message", "").strip()

        if not message:
            flash(text.get("feedback_enter_text"), "error")
            return render("feedback.html", text=text, message=message)

        if len(message) < 10:
            flash(text.get("feedback_min_length"), "error")
            return render("feedback.html", text=text, message=message)

        try:
            with db_connection() as conn:
                conn.execute(
                    "INSERT INTO feedback (user_id, message) VALUES (?, ?)",
                    (session["user_id"], message)
                )

            log_activity(session["user_id"], "submitted feedback")

            flash(text.get("feedback_submitted"), "success")
            return redirect("/dashboard")

        except Exception as e:
            print("Error:", e)
            flash(text.get("feedback_server_error"), "error")

    return render("feedback.html", text=text)


#weather route
@app.route("/weather", methods=["GET", "POST"])
@login_required
def weather():
    weather_data = None

    if request.method == "POST":
        city = request.form.get("city", "").strip()

        if not city:
            flash("Enter city name", "error")
            return render("weather.html")

        api_key = os.getenv("WEATHER_API_KEY")

        if not api_key:
            flash("API key missing", "error")
            return render("weather.html")

        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
            res = requests.get(url, timeout=5)

            if res.status_code == 200:
                data = res.json()
                weather_data = {
                    "city": city,
                    "temperature": data["main"]["temp"],
                    "humidity": data["main"]["humidity"],
                    "description": data["weather"][0]["description"]
                }
            else:
                flash("City not found", "error")

        except Exception as e:
            print(e)
            flash("Weather error", "error")

    return render("weather.html", weather=weather_data)

@app.route("/market", methods=["GET", "POST"])
@login_required
def market():
    """Market prices with real crop data."""
    crops = get_all_crops()
    crops = [{'crop_name': crop[0]} for crop in crops]

    prices = []
    trend = None
    suggestion = None
    selected_crop = None

    if request.method == 'POST':
        selected_crop = request.form.get('crop', '').strip()
    else:
        # Show first crop by default on page load
        if crops:
            selected_crop = crops[0]['crop_name']
    
    if selected_crop:
        # Get price history for the crop
        price_history = get_market_price(selected_crop, 30)
        if price_history:
            prices = [{'date': str(p[2]), 'price': float(p[1])} for p in reversed(price_history)]
        else:
            # no data for this crop
            flash(get_text(get_lang()).get("no_price_data", "No price data available for selected crop"), "info")
            prices = []
        
        # Get trend analysis (only if we have enough data)
        trend_data = get_price_trend(selected_crop, 7)
        if trend_data:
            trend = trend_data['trend']
            # Generate suggestion based on trend
            if trend_data['change_percent'] > 5:
                suggestion = "suggestion_sell"
            elif trend_data['change_percent'] < -5:
                suggestion = "suggestion_wait"
            else:
                suggestion = "suggestion_stable"
        
        log_activity(session["user_id"], f"checked prices for {selected_crop}")

    return render('market.html', crops=crops, prices=prices, selected_crop=selected_crop,
                 trend=trend, suggestion=suggestion)


# ============================================================================
# MARKET PRICE API ENDPOINTS
# ============================================================================

@app.route("/api/market/prices/<crop_name>")
@login_required
def get_crop_prices(crop_name):
    """API endpoint to get market prices for a crop."""
    try:
        prices = get_market_price(crop_name, 30)
        price_data = [{'date': str(p[2]), 'price': float(p[1])} for p in reversed(prices)]
        return {
            'success': True,
            'crop': crop_name,
            'prices': price_data,
            'count': len(price_data)
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}, 400


@app.route("/api/market/crops")
@login_required
def get_crops_list():
    """API endpoint to get all available crops."""
    try:
        crops = get_all_crops()
        crop_list = [crop[0] for crop in crops]
        return {
            'success': True,
            'crops': crop_list,
            'count': len(crop_list)
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}, 400


@app.route("/api/market/trend/<crop_name>")
@login_required
def get_crop_trend(crop_name):
    """API endpoint to get price trend analysis."""
    try:
        trend = get_price_trend(crop_name, 7)
        if trend:
            return {
                'success': True,
                'crop': crop_name,
                'trend': trend
            }
        else:
            return {
                'success': False,
                'error': 'Insufficient data for trend analysis'
            }, 404
    except Exception as e:
        return {'success': False, 'error': str(e)}, 400


@app.route("/admin/market/update-prices", methods=["POST"])
@admin_required
def admin_update_prices():
    """Admin endpoint to update market prices."""
    try:
        data = request.get_json(silent=True)
        if not data:
            data = request.form.to_dict()
        
        # Expected format: {'crop_name': price, 'crop_name2': price2, ...}
        prices_dict = {}
        for key, value in data.items():
            if key != 'csrf_token':  # Skip CSRF token
                try:
                    prices_dict[key] = float(value)
                except (ValueError, TypeError):
                    continue
        
        if update_market_prices(prices_dict):
            flash(f"Updated prices for {len(prices_dict)} crops", "success")
            log_activity(session.get("user_id", 0), "admin_updated_prices")
            return redirect("/admin/market/manage-prices")
        else:
            flash("Error updating prices", "error")
            return redirect("/admin/market/manage-prices")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect("/admin/market/manage-prices")


@app.route("/admin/feedback")
@admin_required
def admin_feedback():
    """Admin dashboard to view feedback."""
    text = get_text(get_lang())
    
    with db_connection() as conn:
        feedbacks = conn.execute("""
            SELECT f.id, f.message, f.created_at, u.name
            FROM feedback f
            JOIN users u ON f.user_id = u.id
            ORDER BY f.created_at DESC
        """).fetchall()
        feedbacks = [dict(f) for f in feedbacks] if feedbacks else []

    return render("admin_feedback.html", feedbacks=feedbacks, text=text)


@app.route("/admin/delete_feedback/<int:id>")
@admin_required
def delete_feedback(id):
    """Delete feedback - admin only."""
    text = get_text(get_lang())
    
    with db_connection() as conn:
        conn.execute("DELETE FROM feedback WHERE id = ?", (id,))
    
    flash(text.get("feedback_deleted", "Feedback deleted."), "success")
    return redirect("/admin/feedback")


@app.route("/view_feedback")
@login_required
def view_feedback():
    """View all user feedback - accessible to all logged-in users."""
    
    try:
        text = get_text(get_lang())
        
        conn = get_db_connection()
        
        feedbacks = conn.execute("""
            SELECT f.id, f.message, f.created_at, u.name
            FROM feedback f
            JOIN users u ON f.user_id = u.id
            ORDER BY f.created_at DESC
        """).fetchall()
        
        feedbacks = [dict(f) for f in feedbacks] if feedbacks else []
        
        return render("view_feedback.html", feedbacks=feedbacks, text=text)
    
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        flash("Error loading feedback.", "error")
        return redirect("/dashboard")


@app.route("/admin/market/manage-prices")
@admin_required
def admin_manage_prices():
    """Admin page to manage market prices."""
    text = get_text(get_lang())
    crops = get_all_crops()
    latest_prices = {}
    
    for crop in crops:
        crop_name = crop[0]
        price_history = get_market_price(crop_name, 1)
        if price_history:
            latest_prices[crop_name] = price_history[0][1]
    
    return render('admin_market.html', crops=crops, latest_prices=latest_prices)


@app.route("/schemes")
@login_required
def schemes():
    """Government schemes - cached for performance."""
    schemes_data = get_all_schemes()
    return render("schemes.html", schemes=schemes_data)


# ============================================================================
# LANGUAGE SUPPORT
# ============================================================================

@app.route("/set_language/<lang>")
def set_language(lang):
    """Set language."""
    if lang in SUPPORTED_LANGS:
        session["lang"] = lang
    return redirect(request.referrer or "/")


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    """404 handler."""
    return render("error.html", error="Page not found"), 404


import traceback


@app.errorhandler(500)
def server_error(e):
    """500 handler."""
    tb = traceback.format_exc()
    print(f"Error: {e}\n{tb}")
    # Show a more descriptive message while still preventing sensitive details
    return render("error.html", error=str(e) or "Server error"), 500


# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    debug = os.getenv("DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=5000, debug=debug)
