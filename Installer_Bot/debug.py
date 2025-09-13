
"""
Create the software_catalouge database and populate it with sample data
"""
import os
import mysql.connector
from dotenv import load_dotenv

def create_database():
    load_dotenv()
    
    # Connect without specifying database first
    config = {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT", 3306)),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    }
    
    try:
        print("🔌 Connecting to MySQL server...")
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        # Create database
        print("📦 Creating database 'software_catalouge'...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS software_catalouge")
        print("✅ Database created successfully!")
        
        # Switch to the new database
        cursor.execute("USE software_catalouge")
        
        # Create table
        print("📋 Creating 'software' table...")
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS software (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            version VARCHAR(50) NOT NULL,
            description TEXT,
            download_url VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_name (name)
        )
        """
        cursor.execute(create_table_sql)
        print("✅ Table created successfully!")
        
        # Check if table is empty
        cursor.execute("SELECT COUNT(*) FROM software")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("📝 Adding sample software data...")
            
            sample_data = [
                ('Google Chrome', '120.0.6099.109', 'Fast and secure web browser'),
                ('Google Chrome', '119.0.6045.199', 'Fast and secure web browser'),
                ('Mozilla Firefox', '121.0', 'Open source web browser'),
                ('Mozilla Firefox', '120.0.1', 'Open source web browser'),
                ('Visual Studio Code', '1.85.1', 'Lightweight code editor'),
                ('Visual Studio Code', '1.84.2', 'Lightweight code editor'),
                ('Python', '3.12.1', 'Programming language'),
                ('Python', '3.11.7', 'Programming language'),
                ('Node.js', '20.10.0', 'JavaScript runtime'),
                ('Node.js', '18.19.0', 'JavaScript runtime'),
                ('Zoom', '5.17.0', 'Video conferencing software'),
                ('Zoom', '5.16.10', 'Video conferencing software'),
                ('Microsoft Teams', '1.6.00.32762', 'Collaboration platform'),
                ('Microsoft Teams', '1.6.00.31281', 'Collaboration platform'),
                ('Docker Desktop', '4.26.1', 'Container platform'),
                ('Docker Desktop', '4.25.2', 'Container platform'),
                ('Git', '2.43.0', 'Version control system'),
                ('Git', '2.42.0', 'Version control system'),
                ('Slack', '4.36.140', 'Team communication tool'),
                ('Slack', '4.35.131', 'Team communication tool'),
            ]
            
            insert_sql = "INSERT INTO software (name, version, description) VALUES (%s, %s, %s)"
            cursor.executemany(insert_sql, sample_data)
            conn.commit()
            
            print(f"✅ Added {len(sample_data)} software entries!")
        else:
            print(f"ℹ️  Table already has {count} records")
        
        # Verify the setup
        cursor.execute("SELECT COUNT(DISTINCT name) as software_count, COUNT(*) as version_count FROM software")
        stats = cursor.fetchone()
        
        print(f"\n📊 Database Setup Complete!")
        print(f"  - Total Software: {stats[0]}")
        print(f"  - Total Versions: {stats[1]}")
        
        # Show sample data
        cursor.execute("SELECT DISTINCT name FROM software ORDER BY name LIMIT 5")
        samples = cursor.fetchall()
        print(f"  - Sample Software: {', '.join([s[0] for s in samples])}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Ready to run your bot! Try: python app.py")
        
    except mysql.connector.Error as err:
        print(f"❌ Error: {err}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    create_database()