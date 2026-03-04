import os
import mysql.connector

from Database.DBConnection import DB_NAME, DB_HOST, DB_USER, DB_PASSWORD
from Database.InsertData import data_insertion


DB_SQL_TEXT = f"""
CREATE DATABASE IF NOT EXISTS `{DB_NAME}`;
"""

TABLE_SQL_TEXT = f"""
USE `{DB_NAME}`;

DROP TABLE IF EXISTS Shipment_Tracking;
DROP TABLE IF EXISTS Costs;
DROP TABLE IF EXISTS Shipments;
DROP TABLE IF EXISTS Courier_Staff;
DROP TABLE IF EXISTS Routes;
DROP TABLE IF EXISTS Warehouses;

CREATE TABLE Courier_Staff (
    Courier_ID VARCHAR(50) PRIMARY KEY,
    Name VARCHAR(150) NOT NULL,
    Rating DECIMAL(3,1) CHECK (Rating BETWEEN 1 AND 5),
    Vehicle_Type VARCHAR(50),
    INDEX idx_courier_staff_vehicle_type (Vehicle_Type),
    INDEX idx_courier_staff_Courier_ID (Courier_ID)
);

CREATE TABLE Shipments (
    Shipment_ID VARCHAR(50) PRIMARY KEY,
    Order_Date DATE NOT NULL,
    Origin VARCHAR(100) NOT NULL,
    Destination VARCHAR(100) NOT NULL,
    Weight DECIMAL(10,2),
    Courier_ID VARCHAR(50),
    Status VARCHAR(50),
    Delivery_Date DATE NULL,

    CONSTRAINT FK_Shipments_Courier
        FOREIGN KEY (Courier_ID)
        REFERENCES Courier_Staff(Courier_ID),
    INDEX idx_shipments_origin_destination (Origin, Destination),
    INDEX idx_shipments_courier_id (Courier_ID),
    INDEX idx_shipments_order_date (Order_Date)
);

CREATE TABLE Shipment_Tracking (
    Tracking_ID INT PRIMARY KEY,
    Shipment_ID VARCHAR(50) NOT NULL,
    Status VARCHAR(50),
    Timestamp DATETIME NOT NULL,

    CONSTRAINT FK_Tracking_Shipment
        FOREIGN KEY (Shipment_ID)
        REFERENCES Shipments(Shipment_ID),
    INDEX idx_tracking_shipment_id (Shipment_ID),
    INDEX idx_tracking_status (Status)
);

CREATE TABLE Costs (
    Costs_ID INT PRIMARY KEY AUTO_INCREMENT,
    Shipment_ID VARCHAR(50) NOT NULL,
    Fuel_Cost DECIMAL(15,2),
    Labor_Cost DECIMAL(15,2),
    Misc_Cost DECIMAL(15,2),

    CONSTRAINT FK_Costs_Shipment
        FOREIGN KEY (Shipment_ID)
        REFERENCES Shipments(Shipment_ID),
    INDEX idx_costs_shipment_id (Shipment_ID)
);

CREATE TABLE Routes (
    Route_ID VARCHAR(50) PRIMARY KEY,
    Origin VARCHAR(100) NOT NULL,
    Destination VARCHAR(100) NOT NULL,
    Distance_KM DECIMAL(10,2),
    Avg_Time_Hours DECIMAL(5,2),
    INDEX idx_routes_origin_destination (Origin, Destination)
);

CREATE TABLE Warehouses (
    Warehouse_ID VARCHAR(50) PRIMARY KEY,
    City VARCHAR(100) NOT NULL,
    State VARCHAR(50),
    Capacity INT
);
"""

def get_server_connection():
    return mysql.connector.connect(
        host = DB_HOST,
        user = DB_USER,
        password = DB_PASSWORD,
    )

def execute_sql_script(cursor, sql_text: str):
    statements = [stmt.strip() for stmt in sql_text.split(";") if stmt.strip()]
    for statement in statements:
        cursor.execute(statement)

def create_database_and_tables():
    with get_server_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(DB_SQL_TEXT)

            execute_sql_script(cursor, TABLE_SQL_TEXT)

        conn.commit()

try:
    create_database_and_tables()
    print("Database and tables created successfully.")

    # Insert data to the tables
    data_insertion()
except mysql.connector.Error as error:
    print(f"Database setup failed: {error}")
