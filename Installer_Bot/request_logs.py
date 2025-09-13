import os
import mysql.connector
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

try:
    # Connect to MySQL
    connection = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

    cursor = connection.cursor()

    # Drop old table if structure is different (optional: only if you want fresh structure)
    # cursor.execute("DROP TABLE IF EXISTS request_logging")
    # print("Deleted")

    #  Create table with correct structure
    create_table_query = """
    CREATE TABLE IF NOT EXISTS request_logging (
        incident_id VARCHAR(100) NOT NULL,
        software_name VARCHAR(255) NOT NULL,
        version_name VARCHAR(100) NOT NULL,
        status VARCHAR(256) NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        feedback text
    );
    """

    cursor.execute(create_table_query)
    connection.commit()

    print("✅ request_logging table created/verified successfully!")

except mysql.connector.Error as err:
    print(f"❌ Error: {err}")

finally:
    if cursor:
        cursor.close()
    if connection:
        connection.close()
