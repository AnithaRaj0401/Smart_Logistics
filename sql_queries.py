# Centralized SQL queries for Dashboard

Q_DISTINCT_ORIGINS = "SELECT DISTINCT Origin FROM shipments ORDER BY Origin"
Q_DISTINCT_DESTINATIONS = "SELECT DISTINCT Destination FROM shipments ORDER BY Destination"
Q_DISTINCT_COURIERS = "SELECT DISTINCT Courier_ID FROM shipments ORDER BY Courier_ID"
Q_DISTINCT_SHIPMENTS = "SELECT DISTINCT Shipment_ID FROM shipments ORDER BY Shipment_ID"

Q_AVG_DELIVERY_TIME_PER_ROUTE = """
    SELECT
        Origin,
        Destination,
        ROUND(AVG(DATEDIFF(Delivery_Date, Order_Date)), 2) AS Avg_Delivery_Days
    FROM Shipments
    WHERE Delivery_Date IS NOT NULL
    GROUP BY Origin, Destination
    ORDER BY Avg_Delivery_Days DESC
"""

Q_MOST_DELAYED_ROUTES = """
    SELECT
        r.Route_ID,
        r.Origin,
        r.Destination,
        COUNT(s.Shipment_ID) AS Total_Deliveries,
        ROUND(AVG(
            GREATEST(
                TIMESTAMPDIFF(HOUR, s.Order_Date, s.Delivery_Date) - r.Avg_Time_Hours,
                0
            )
        ), 2) AS Avg_Delay_Hours,
        ROUND(MAX(
            GREATEST(
                TIMESTAMPDIFF(HOUR, s.Order_Date, s.Delivery_Date) - r.Avg_Time_Hours,
                0
            )
        ), 2) AS Max_Delay_Hours
    FROM Routes r
    JOIN Shipments s
        ON s.Origin = r.Origin
      AND s.Destination = r.Destination
    WHERE s.Delivery_Date IS NOT NULL
    GROUP BY r.Route_ID, r.Origin, r.Destination
    HAVING Avg_Delay_Hours > 0
    ORDER BY Avg_Delay_Hours DESC, Total_Deliveries DESC
"""

Q_OVERALL_DELIVERY_TIME_DISTANCE = """
  SELECT
      r.Route_ID,
      r.Origin,
      r.Destination,
      r.Distance_KM,
      ROUND(AVG(TIMESTAMPDIFF(HOUR, s.Order_Date, s.Delivery_Date)), 2) AS Avg_Actual_Delivery_Hours,
      ROUND(r.Avg_Time_Hours, 2) AS Expected_Delivery_Hours,
      ROUND(
          AVG(TIMESTAMPDIFF(HOUR, s.Order_Date, s.Delivery_Date)) - r.Avg_Time_Hours,
          2
      ) AS Avg_Delay_Hours
  FROM Routes r
  JOIN Shipments s
      ON s.Origin = r.Origin
    AND s.Destination = r.Destination
  WHERE s.Delivery_Date IS NOT NULL
  GROUP BY r.Route_ID, r.Origin, r.Destination, r.Distance_KM, r.Avg_Time_Hours
  ORDER BY r.Distance_KM;
"""

Q_DISTINCT_VEHICLES = "SELECT DISTINCT Vehicle_Type FROM courier_staff ORDER BY Vehicle_Type"

Q_AVG_DELIVERY_TIME_TREND = """
      SELECT
          s.Order_Date,
          ROUND(AVG(TIMESTAMPDIFF(HOUR, s.Order_Date, s.Delivery_Date)), 2) AS Avg_Delivery_Hours
      FROM Shipments s
      WHERE s.Delivery_Date IS NOT NULL
      GROUP BY s.Order_Date
      ORDER BY s.Order_Date
  """
Q_COST_KPI = """
        SELECT SUM(Fuel_Cost) AS Fuel_Costs
            , SUM(Labor_Cost) AS Labor_Costs
            , SUM(Misc_Cost) AS Misc_Costs
        FROM shipments s
          JOIN shipment_tracking t ON s.Shipment_ID = t.Shipment_ID
            JOIN costs c ON s.Shipment_ID = c.Shipment_ID
        WHERE t.Status = 'Delivered';  
     """

def q_destinations_by_origins(origin_count: int) -> str:
    placeholders = ",".join(["%s"] * origin_count)
    return f"SELECT DISTINCT Destination FROM shipments WHERE Origin IN ({placeholders}) ORDER BY Destination"

def build_shipment_query(origin_filter, destination_filter, courier_filter, date_from, date_to, shipment_id=None):
    query = """
    SELECT s.Shipment_ID, s.Order_Date, s.Origin, s.Destination,
           s.Weight, s.Courier_ID, s.Status, s.Delivery_Date,
           c.Name AS Courier_Name
    FROM shipments s
    JOIN courier_staff c ON s.Courier_ID = c.Courier_ID
    """
    where_clauses = []
    params = []

    if shipment_id:
        where_clauses.append(f"s.Shipment_ID LIKE %s")
        params.append(f"%{shipment_id}%")

    if origin_filter:
        where_clauses.append(f"s.Origin IN ({','.join(['%s'] * len(origin_filter))})")
        params.extend(origin_filter)

    if destination_filter:
        where_clauses.append(f"s.Destination IN ({','.join(['%s'] * len(destination_filter))})")
        params.extend(destination_filter)

    if courier_filter and courier_filter != "All":
        where_clauses.append("s.Courier_ID = %s")
        params.append(courier_filter)

    if date_from and date_to:
        where_clauses.append("DATE(s.Order_Date) BETWEEN %s AND %s")
        params.extend([date_from, date_to])
    elif date_from:
        where_clauses.append("DATE(s.Order_Date) >= %s")
        params.append(date_from)
    elif date_to:
        where_clauses.append("DATE(s.Order_Date) <= %s")
        params.append(date_to)

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += " ORDER BY s.Order_Date DESC, s.Shipment_ID DESC;"
    return query, params


def build_courier_shipment_query(courier_filter, name_search, vehicle_filter):
    query = """
    SELECT
        s.Courier_ID,
        c.Name AS Courier_Name,
        c.Vehicle_Type,
        COUNT(*) AS Shipments_Handled
    FROM Shipments s
    JOIN Courier_Staff c ON c.Courier_ID = s.Courier_ID
    """
    where_clauses = []
    params = []

    if courier_filter:
        where_clauses.append(f"s.Courier_ID IN ({','.join(['%s'] * len(courier_filter))})")
        params.extend(courier_filter)

    if name_search:
        where_clauses.append(f"c.Name LIKE %s")
        params.append(f"%{name_search}%")
    
    if vehicle_filter:
        where_clauses.append(f"c.Vehicle_Type IN ({','.join(['%s'] * len(vehicle_filter))})")
        params.extend(vehicle_filter)

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += " GROUP BY s.Courier_ID, c.Name"
    query += " ORDER BY Shipments_Handled DESC;"

    return query, params


def build_courier_delivery_query(courier_filter, name_search, vehicle_filter):
    query = """
      SELECT
        s.Courier_ID,
        c.Name AS Courier_Name,
        c.Vehicle_Type,
        COUNT(*) AS Total_Shipments,
        SUM(CASE WHEN s.Status = 'Delivered' THEN 1 ELSE 0 END) AS Delivered_Shipments,
        SUM(CASE 
            WHEN s.Delivery_Date IS NOT NULL 
            AND TIMESTAMPDIFF(HOUR, s.Order_Date, s.Delivery_Date) <= r.Avg_Time_Hours 
            THEN 1 
            ELSE 0 
        END) AS On_Time_Deliveries,
        ROUND(
            (SUM(CASE 
                WHEN s.Delivery_Date IS NOT NULL 
                AND TIMESTAMPDIFF(HOUR, s.Order_Date, s.Delivery_Date) <= r.Avg_Time_Hours 
                THEN 1 
                ELSE 0 
            END) * 100.0) / SUM(CASE WHEN s.Status = 'Delivered' THEN 1 ELSE 0 END),
            2
        ) AS On_Time_Delivery_Percent
    FROM Shipments s
    JOIN Courier_Staff c ON c.Courier_ID = s.Courier_ID
    JOIN Routes r ON r.Origin = s.Origin AND r.Destination = s.Destination
    """
    where_clauses = []
    params = []

    if courier_filter:
        where_clauses.append(f"s.Courier_ID IN ({','.join(['%s'] * len(courier_filter))})")
        params.extend(courier_filter)

    if name_search:
        where_clauses.append(f"c.Name LIKE %s")
        params.append(f"%{name_search}%")

    if vehicle_filter:
        where_clauses.append(f"c.Vehicle_Type IN ({','.join(['%s'] * len(vehicle_filter))})")
        params.extend(vehicle_filter)

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += " GROUP BY s.Courier_ID, c.Name"
    query += " ORDER BY On_Time_Deliveries DESC;"

    return query, params


def build_courier_query(courier_filter, name_search, vehicle_filter):
    query = """
      SELECT
        c.Courier_ID,
        c.Name AS Courier_Name,
        c.Rating,
        CASE
            WHEN rating >= 4.5 THEN 'Excellent'
            WHEN rating >= 3.5 THEN 'Good'
            WHEN rating >= 2.5 THEN 'Average'
            ELSE 'Needs Improvement'
        END AS performance_category,
        c.Vehicle_Type
    FROM Courier_Staff c 
    """
    where_clauses = []
    params = []

    if courier_filter:
        where_clauses.append(f"c.Courier_ID IN ({','.join(['%s'] * len(courier_filter))})")
        params.extend(courier_filter)

    if name_search:
        where_clauses.append(f"c.Name LIKE %s")
        params.append(f"%{name_search}%")

    if vehicle_filter:
        where_clauses.append(f"c.Vehicle_Type IN ({','.join(['%s'] * len(vehicle_filter))})")
        params.extend(vehicle_filter)

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += " ORDER BY c.Rating DESC;"

    return query, params


def build_shipmentcost_query(shipmentID_filter):
    query = """
      SELECT
          c.Shipment_ID,
          Fuel_Cost,
          Labor_Cost, 
          Misc_Cost,
          ROUND(COALESCE(c.Fuel_Cost,0) + COALESCE(c.Labor_Cost,0) + COALESCE(c.Misc_Cost,0), 2) AS Total_Cost
      FROM Costs c
    """
    where_clauses = []
    params = []

    if shipmentID_filter:
        where_clauses.append(f"c.Shipment_ID IN ({','.join(['%s'] * len(shipmentID_filter))})")
        params.extend(shipmentID_filter)

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += " ORDER BY Total_Cost DESC;"

    return query, params

def build_routecost_query():
    # Base query: route-wise cost summary
    query = """
      SELECT
          r.Route_ID,
          r.Origin,
          r.Destination,
          COUNT(*) AS Shipment_Count,
          ROUND(SUM(COALESCE(c.Fuel_Cost,0) + COALESCE(c.Labor_Cost,0) + COALESCE(c.Misc_Cost,0)), 2) AS Total_Cost
      FROM Costs c
      JOIN Shipments s ON s.Shipment_ID = c.Shipment_ID
      JOIN Routes r
        ON r.Origin = s.Origin
       AND r.Destination = s.Destination
      GROUP BY r.Route_ID, r.Origin, r.Destination
      ORDER BY Total_Cost DESC
    """
    return query

def build_cancellation_origin_query():
    query = """
        SELECT
            s.Origin,
            COUNT(*) AS Total_Shipments,
            SUM(CASE WHEN s.Status = 'Cancelled' THEN 1 ELSE 0 END) AS Cancelled_Shipments,
            ROUND(
                100.0 * SUM(CASE WHEN s.Status = 'Cancelled' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0),
                2
            ) AS Cancellation_Rate_Percent
        FROM Shipments s
        GROUP BY s.Origin
        ORDER BY Cancellation_Rate_Percent DESC, Total_Shipments DESC;
    """
    return query

def build_cancellation_courier_query():
    query = """
        SELECT
            s.Courier_ID,
            c.Name AS Courier_Name,
            COUNT(*) AS Total_Shipments,
            SUM(CASE WHEN s.Status = 'Cancelled' THEN 1 ELSE 0 END) AS Cancelled_Shipments,
            ROUND(
                100.0 * SUM(CASE WHEN s.Status = 'Cancelled' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0),
                2
            ) AS Cancellation_Rate_Percent
        FROM Shipments s
        JOIN Courier_Staff c ON c.Courier_ID = s.Courier_ID
        GROUP BY s.Courier_ID, c.Name
        ORDER BY Cancellation_Rate_Percent DESC, Total_Shipments DESC;
    """
    return query

    
def build_warehouse_query():
    query = """
      SELECT Warehouse_ID, City, State, Capacity
      FROM warehouses 
      ORDER BY Capacity DESC;
    """
    return query