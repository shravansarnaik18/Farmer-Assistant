from db import init_database, db_connection
from werkzeug.security import generate_password_hash

def setup_database():
    print("Initializing database...")
    init_database()

    with db_connection() as conn:
        # crops
        conn.executemany(
            "INSERT OR IGNORE INTO crops (crop_name, season, soil_type, fertilizer, pest_control) VALUES (?,?,?,?,?)",
            [
                ("Wheat", "Rabi", "Loamy", "NPK 10:26:26", "Aphids"),
                ("Rice", "Kharif", "Clay", "NPK 20:10:10", "Stem borer"),
            ]
        )

        # admin
        existing = conn.execute("SELECT 1 FROM admins LIMIT 1").fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO admins (username, password) VALUES (?,?)",
                ("admin", generate_password_hash("admin"))
            )

        conn.commit()

    print("✓ Database setup complete")

if __name__ == "__main__":
    setup_database()