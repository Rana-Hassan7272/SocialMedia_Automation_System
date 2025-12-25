"""
Quick script to initialize the database.
Run this after setting up your environment.
"""

from src.database import DatabaseManager


def main():
    """Initialize the database with all tables."""
    print("🔧 Initializing database...")
    
    db = DatabaseManager()
    db.initialize_database()
    
    print("\n✅ Database setup complete!")
    print(f"📁 Database location: {db.database_url}")
    print("\nYou can now start using the system.")


if __name__ == "__main__":
    main()
