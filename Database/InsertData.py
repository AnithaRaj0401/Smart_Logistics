# CSV to Table and MySQL insertion
import pandas as pd 
from .DBConnection import get_server_connection

def clear_all_table():
    """Delete all existing records from tables and reset auto-increment counters"""
    conn = get_server_connection()
    cursor = conn.cursor()

    # Delete all rows from each table
    cursor.execute(f"DELETE FROM routes")
    cursor.execute(f"DELETE FROM warehouses")
    cursor.execute(f"DELETE FROM costs")
    cursor.execute(f"DELETE FROM shipment_tracking")
    cursor.execute(f"DELETE FROM shipments")
    cursor.execute(f"DELETE FROM courier_staff")

    # Reset auto-increment counters to 1
    cursor.execute(f"ALTER TABLE costs AUTO_INCREMENT = 1")

    print(f"All rows deleted from all tables ")
    conn.close()


def insert_data_to_mysql(df, table_name):
    """Insert dataframe records into the specified MySQL table"""
    conn = get_server_connection()
    cursor = conn.cursor()

    # Prepare the SQL insert statement with column names and placeholders
    fieldName = ', '.join(df.columns)
    fieldValue = ', '.join(['%s'] * len(df.columns))
    sql = f"INSERT INTO {table_name} ({fieldName}) VALUES ({fieldValue})"

    # Convert dataframe rows to tuples for bulk insert
    data = [tuple(row) for row in df.values]

    # Bulk insert all rows in one call
    cursor.executemany(sql, data)

    # Commit changes and close connections
    conn.commit()
    cursor.close()
    conn.close()

def get_csv_data_insert(file_path, tableName):
    """Read CSV file and insert data into specified table"""
    try:
        # Read CSV file into pandas dataframe
        table = pd.read_csv(file_path)
        insert_data_to_mysql(table, tableName)

        print(f"Successfully inserted csv data into {tableName}")
    except Exception as e:
        print(f"Failed to insert data: {e}")


def get_json_data_insert(file_path, tableName):
    """Read JSON file and insert data into specified table"""
    try:
        # Read JSON file into pandas dataframe
        table = pd.read_json(file_path, orient=None, lines=False)
        insert_data_to_mysql(table, tableName)

        print(f"Successfully inserted JSON data into {tableName}")
    except Exception as e:
        print(f"Failed to insert JSON data: {e}")


def data_insertion():
    """Main function to clear tables and load data from CSV and JSON files"""
    
    # Main execution: Clear tables and load data from CSV and JSON files
    clear_all_table()

    # Load route data from CSV
    get_csv_data_insert('DataSets/routes.csv', "routes")

    # Load warehouse data from JSON
    get_json_data_insert('DataSets/warehouses.json', "warehouses")

    # Load courier staff data from CSV
    get_csv_data_insert('DataSets/courier_staff.csv', "courier_staff")

    # Load shipment data from JSON
    get_json_data_insert('DataSets/shipments.json', "shipments")

    # Load cost data from CSV
    get_csv_data_insert('DataSets/costs.csv', "costs")

    # Load shipment tracking data from CSV
    get_csv_data_insert('DataSets/shipment_tracking.csv', "shipment_tracking")

