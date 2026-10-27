# init_db.py – Run this script to initialize the local SQLite database safely.
# It creates the database file (if it does not exist) and runs migrations.
# Existing data is preserved; tables are created only if missing.

if __name__ == "__main__":
    from backend.database import init_db
    init_db()
    print("Database initialization completed.")
