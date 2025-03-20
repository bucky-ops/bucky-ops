import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    # Connect to PostgreSQL server
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password='7459',
        host='localhost',
        port='5432'
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
    # Create a cursor object
    cursor = conn.cursor()
    
    try:
        # Create the database
        cursor.execute('CREATE DATABASE file_management')
        print("Database created successfully!")
    except psycopg2.Error as e:
        print(f"Error creating database: {e}")
    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()

if __name__ == '__main__':
    create_database() 