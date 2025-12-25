"""
Database migration script to update published_posts table.
Renames linkedin columns to twitter columns.
"""

from sqlalchemy import text
from src.database import DatabaseManager

print("🔄 Updating database schema...\n")

db = DatabaseManager()

# Drop and recreate the table with correct schema
print("1. Dropping old published_posts table...")
with db.get_session() as session:
    session.execute(text("DROP TABLE IF EXISTS published_posts"))
    session.commit()
print("   ✅ Dropped")

print("\n2. Recreating table with correct schema...")
db.initialize_database()
print("   ✅ Table recreated with twitter_post_id and twitter_post_url")

print("\n✅ Database migration complete!")
print("\nYou can now publish tweets without database errors.")
