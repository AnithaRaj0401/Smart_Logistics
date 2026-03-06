Smart Logistics Management & Analytics Platform
==================================================
This project builds a centralized Smart Logistics Management and Analytics Platform that consolidates operational data into a MySQL database 
and provides an interactive Streamlit dashboard for real-time analytics and decision-making.

Project Objective
------------------
The objective of this project is to design and implement an end-to-end logistics analytics system that:
•	Processes large-scale logistics datasets
•	Stores data in a normalized MySQL relational database
•	Provides operational insights using Streamlit dashboards
•	Supports KPI monitoring and performance evaluation

Key Features
-------------
•	Centralized logistics database
•	Shipment tracking & monitoring
•	Courier performance analytics
•	Delivery delay analysis
•	Route efficiency insights
•	Operational cost monitoring
•	Interactive analytics dashboard
•	KPI-based performance evaluation

Prerequisites
-----------------
1. Python 3.9+
2. MySQL Server running locally
3. Python packages:
   - pandas
   - mysql-connector-python
   - streamlit
   - plotly

Technology Stack    		Layer Technology
-----------------------------------------
Frontend Dashboard		  Streamlit
Backend	            		Python
Database	          		MySQL
Data Processing	       	Pandas
Query Language	   	    SQL
Visualization	      		Streamlit Charts

Analytics & KPIs
-----------------
The dashboard provides insights such as:
•	Shipments handled per courier
•	On-time delivery percentage
•	Average delivery delay
•	Route performance analysis
•	Warehouse utilization
•	Cost breakdown analysis
•	Shipment status distribution

Project Files
-------------
- DatabaseSetup.py    -> Creates MySQL database and tables.
- InsertData.py       -> Loads CSV/JSON dataset files into MySQL tables.
- Dashboard.py        -> Streamlit dashboard for analytics and operations.
- sql_queries.py      -> Centralized SQL query definitions.

How to Run
----------
1. Create database and tables:
   Insert dataset records:
      py -m Database.DatabaseSetup

2. Start dashboard:
      streamlit run Dashboard.py

Dataset Location
----------------
Keep dataset files under:
- DataSets

Notes
-----
- Need to ensure MySQL service is running before executing scripts.
- If table data already exists, InsertData.py clears and reloads tables.

