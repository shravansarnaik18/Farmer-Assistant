import sqlite3
import datetime
import random

from db import init_database, get_db_connection


def seed_market_prices():
    """Populate initial market prices for all crops."""

    # Initialize database
    init_database()

    # Sample realistic market prices (₹/Quintal)
    market_prices = {
        'Wheat': 2200,
        'Rice': 2800,
        'Barley': 2000,
        'Gram (Chickpea)': 4500,
        'Peas': 3500,
        'Maize': 1800,
        'Jowar': 1500,
        'Cotton': 5500,
        'Moong': 4800,
        'Masoor': 5000,
        'Arhar': 4800,
        'Urad': 5200,
        'Groundnut': 4500,
        'Soybean': 3500,
        'Sunflower': 3800,
        'Rapeseed': 4200,
        'Chilli': 3500,
        'Turmeric': 6500,
        'Cumin': 5500,
        'Coriander': 4500,
        'Tomato': 1200,
        'Onion': 1500,
        'Potato': 1000,
        'Cabbage': 800,
        'Carrot': 900,
        'Cucumber': 700,
        'Sugarcane': 280,
        'Mango': 2500,
        'Banana': 1200,
        'Coconut': 1500
    }

    today = datetime.date.today()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # OPTIONAL: clear old data
        # cursor.execute("DELETE FROM market_prices")

        # Insert data for last 7 days
        for day_offset in range(7, 0, -1):
            price_date = today - datetime.timedelta(days=day_offset)

            for crop_name, base_price in market_prices.items():
                variation = random.uniform(0.95, 1.05)
                current_price = round(base_price * variation, 2)

                cursor.execute(
                    """
                    INSERT INTO market_prices (crop_name, price, date)
                    VALUES (?, ?, ?)
                    """,
                    (crop_name, current_price, price_date)
                )

        conn.commit()

        print("✓ Successfully populated market prices")
        print(f"✓ Crops count: {len(market_prices)}")
        print(f"✓ Data added till: {today}")

    except sqlite3.Error as e:
        conn.rollback()
        print(f"✗ Database error: {e}")

    except Exception as e:
        conn.rollback()
        print(f"✗ Unexpected error: {e}")

    finally:
        conn.close()


if __name__ == "__main__":
    print("Starting market price data population...")
    seed_market_prices()
    print("✓ Market data seeding complete!")