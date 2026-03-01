import pandas as pd
import streamlit as st
import mysql.connector
import plotly.express as px
from sql_queries import (
    Q_DISTINCT_ORIGINS,
    Q_DISTINCT_DESTINATIONS,
    Q_DISTINCT_COURIERS,
    Q_AVG_DELIVERY_TIME_PER_ROUTE,
    Q_DISTINCT_SHIPMENTS,
    Q_DISTINCT_VEHICLES,
    Q_MOST_DELAYED_ROUTES,
    Q_OVERALL_DELIVERY_TIME_DISTANCE,
    build_cancellation_courier_query,
    build_cancellation_origin_query,
    build_courier_delivery_query,
    build_courier_query,
    build_routecost_query,
    build_shipmentcost_query,
    build_warehouse_query,
    q_destinations_by_origins,
    build_shipment_query,
    build_courier_shipment_query
)

st.set_page_config(
    page_title="Smart Logistics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Smart Logistics Management & Analytics Platform")

st.write("This dashboard provides insights into the logistics operations, including delivery performance, inventory management, and route optimization. Use the sidebar to navigate through different sections and explore the data visualizations and analytics.")

def get_connection():
    """Establish and return a MySQL database connection"""
    try:
        return mysql.connector.connect(
            host = "localhost",
            user = "root",
            password = "root",
            database = "logistics"
        )
    except mysql.connector.Error as error:
        st.error(f"Database connection failed: {error}")
        return None

def fetch_data(query, params=None):
    """Fetch data from the database based on the provided SQL query"""
    conn = None
    try:
        conn = get_connection()
        if conn is None:
            return pd.DataFrame()

        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as error:
        st.error(f"Query execution failed: {error}")
        return pd.DataFrame()
    finally:
        if conn is not None:
            conn.close()

#Side bar for navigation
st.sidebar.title("Dashboard Features")
options = ["Shipment Details", "Operational KPIs", "Analytical Views"]  
selection = st.sidebar.radio("Select a features", options)

if selection == "Shipment Details":
  st.subheader("Shipment Details")

  st.sidebar.subheader("Shipments Filters")
  
  # Search box for Shipment ID   
  shipment_Id = st.sidebar.text_input("Search by Shipment ID", key="shipment_id_search")
  
  # Add filters : Origin, Destination, Courier ID for shipment details 
  origin_filter = st.sidebar.multiselect(
      "Origin", 
      options = fetch_data(Q_DISTINCT_ORIGINS)['Origin'])

  if origin_filter:
      destinations_df = fetch_data(q_destinations_by_origins(len(origin_filter)), params=origin_filter)
  else:
      destinations_df = fetch_data(Q_DISTINCT_DESTINATIONS)

  destination_filter = st.sidebar.multiselect(
        "Destination",
        options = destinations_df["Destination"].tolist(),
    )  
  
  courier_options = fetch_data(Q_DISTINCT_COURIERS)["Courier_ID"].tolist()
  courier_filter = st.sidebar.selectbox(
      "Courier ID",
      options=["All"] + courier_options
  )

  # Add date range filter for Order Date
  st.sidebar.subheader("Filter by Order Date")
  date_From = st.sidebar.date_input("Order Date From", value = None)
  date_To = st.sidebar.date_input("Order Date To", value = None)

  # Build shipment query safely based on selected filters
  shipment_query, params = build_shipment_query(
      origin_filter=origin_filter,
      destination_filter=destination_filter,
      courier_filter=courier_filter,
      date_from=date_From,
      date_to=date_To,
      shipment_id=shipment_Id
  )

  # Execute with params only when placeholders exist
  shipment_data = fetch_data(shipment_query, params=params if params else None)
  # Display result in UI
  st.dataframe(shipment_data, width='stretch', height=700)

elif selection == "Operational KPIs":
  st.subheader("Operational KPIs")

  # Add pie chart for shipment status distribution
  st.subheader("Shipment Status Distribution")

  # Build KPI query to fetch counts for Delivered, Cancelled, and Active shipments
  kpi_query = """
    SELECT
      (SELECT COUNT(*) FROM Shipments) AS Total_Shipments,
      (SELECT COUNT(*) FROM Shipment_Tracking WHERE Status = 'Delivered') AS Delivered_Shipments,
      (SELECT COUNT(*) FROM Shipment_Tracking WHERE Status = 'Cancelled') AS Cancelled_Shipments,
      (SELECT COUNT(*) FROM Shipments) - (SELECT COUNT(*) FROM Shipment_Tracking WHERE Status IN ('Delivered', 'Cancelled')) AS Active_Shipments;
  """
  # Fetch KPI data for pie chart
  kpi_data = fetch_data(kpi_query)

  # Create pie chart using Plotly Express
  if not kpi_data.empty:
    pie_df = pd.DataFrame({
        "Category": ["Delivered_Shipments", "Cancelled_Shipments", "Active_Shipments"],
        "Count": [
            int(kpi_data.loc[0, "Delivered_Shipments"] or 0),
            int(kpi_data.loc[0, "Cancelled_Shipments"] or 0),
            int(kpi_data.loc[0, "Active_Shipments"] or 0),
        ],
    })

    fig = px.pie(
        pie_df,
        names="Category",
        values="Count",
        title="",
        hole=0.3
    )

    # Show numbers (count), not %
    fig.update_traces(
        textinfo="value",
        hovertemplate="%{label}: %{value}<extra></extra>"
    ) 

    st.plotly_chart(fig)

    # Add bar chart for cost distribution of Delivered shipments
    st.subheader("Delivered Shipment Cost Distribution")

    # Build KPI query to fetch total costs for Delivered shipments
    kpi_query = """
        SELECT SUM(Fuel_Cost) AS Fuel_Costs
          , SUM(Labor_Cost) AS Labor_Costs
            , SUM(Misc_Cost) AS Misc_Costs
        FROM shipments s
          JOIN shipment_tracking t ON s.Shipment_ID = t.Shipment_ID
            JOIN costs c ON s.Shipment_ID = c.Shipment_ID
        WHERE t.Status = 'Delivered';  
     """
    # Fetch KPI data for bar chart
    kpi_data = fetch_data(kpi_query)

    # Create bar chart using Plotly Express
    if not kpi_data.empty:
        bar_df = pd.DataFrame({
            "Category": ["Fuel_Costs", "Labor_Costs", "Misc_Costs"],
            "Amount": [
                float(kpi_data.loc[0, "Fuel_Costs"] or 0),
                float(kpi_data.loc[0, "Labor_Costs"] or 0),
                float(kpi_data.loc[0, "Misc_Costs"] or 0),
            ],
        })

        fig = px.bar(
            bar_df,
            x="Category",
            y="Amount",
            color="Category",
            text="Amount",
            title=""
        )
        fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig.update_layout(showlegend=False)

        st.plotly_chart(fig, width=600)
        
        # Add line chart for average delivery time trend
        st.subheader("Average Delivery Time Trend")

        avg_delivery_query = """
            SELECT
                s.Order_Date,
                ROUND(AVG(TIMESTAMPDIFF(HOUR, s.Order_Date, s.Delivery_Date)), 2) AS Avg_Delivery_Hours
            FROM Shipments s
            WHERE s.Delivery_Date IS NOT NULL
            GROUP BY s.Order_Date
            ORDER BY s.Order_Date
        """
        # Fetch data for average delivery time trend
        avg_delivery_df = fetch_data(avg_delivery_query)

        # Create line chart using Plotly Express
        if not avg_delivery_df.empty:
            fig = px.line(
                avg_delivery_df,
                x="Order_Date",
                y="Avg_Delivery_Hours",
                markers=True,
                title=""
            )
            st.plotly_chart(fig, width='stretch')
  
elif selection == "Analytical Views":
  # Radio buttons for selecting different analytical views
  options = [" 1. Delivery Performance Insights", " 2. Courier Performance", " 3. Cost Analytics", " 4. Cancellation Analysis", " 5. Warehouse Insights"]  
  analytical_selection = st.sidebar.radio("Select Analytical View Option", options)

  if analytical_selection == " 1. Delivery Performance Insights":
    st.subheader("Delivery Performance Insights")
    st.subheader("1. Average delivery time per route")
    # Fetch data for Average delivery time per route
    route_data = fetch_data(Q_AVG_DELIVERY_TIME_PER_ROUTE)
    st.dataframe(route_data, width=600)

    st.subheader("2. Most delayed routes");
    # Fetch data for Most delayed routes
    route_data = fetch_data(Q_MOST_DELAYED_ROUTES)
    st.dataframe(route_data, 900)

    st.subheader("3. Delivery time vs distance comparison");
    # Fetch data for delivery time vs distance comparison
    route_data = fetch_data(Q_OVERALL_DELIVERY_TIME_DISTANCE)
    st.dataframe(route_data)
 
  elif analytical_selection == " 2. Courier Performance":
    st.header("Courier Performance")
  
    courier_options = fetch_data(Q_DISTINCT_COURIERS)["Courier_ID"].tolist()
    courier_filter = st.sidebar.multiselect(
        "Courier ID",
        options=["All"] + courier_options
    )
 
    name_search = st.sidebar.text_input("Search by Courier Name", key="courier_name_search")
      
    vehicle_options = fetch_data(Q_DISTINCT_VEHICLES)["Vehicle_Type"].tolist()
    vehicle_filter = st.sidebar.multiselect(
        "Vehicle Type",
        options= vehicle_options
    )

    # Build shipment query safely based on selected filters
    st.subheader("1. Shipments handled per courier");
    courier_query, params = build_courier_shipment_query(
        courier_filter = courier_filter,
        name_search = name_search,
        vehicle_filter = vehicle_filter
    )

    courier_data = fetch_data(courier_query, params=params if params else None)
    st.dataframe(courier_data, width = 600 )
    
    # Build On-time delivery query safely based on selected filters
    st.subheader("2. On-time delivery %");
    courier_query, params = build_courier_delivery_query(
        courier_filter = courier_filter,
        name_search = name_search,
        vehicle_filter = vehicle_filter
    )
    courier_data = fetch_data(courier_query, params=params if params else None)
    st.dataframe(courier_data, width = 900 )

    # Build On-time delivery query safely based on selected filters
    st.subheader("3. Rating Comparison");
    courier_query, params = build_courier_query(
        courier_filter = courier_filter,
        name_search = name_search,
        vehicle_filter = vehicle_filter
    )
    courier_data = fetch_data(courier_query, params=params if params else None)
    st.dataframe(courier_data, width = 900 )
    
  elif analytical_selection == " 3. Cost Analytics":
    st.header("Cost Analytics")

    shipment_option = fetch_data(Q_DISTINCT_SHIPMENTS)["Shipment_ID"].tolist()
    shipmentID_filter = st.sidebar.multiselect(
        "Shipment ID",
        options = shipment_option
    )
 
    # Build shipment query safely based on selected filters
    st.subheader("1. Total cost per shipment");
    cost_query, params = build_shipmentcost_query(
        shipmentID_filter = shipmentID_filter ,
    )

    cost_data = fetch_data(cost_query, params=params if params else None)
    st.dataframe(cost_data, width = 600 )
    
    # Build shipment query safely based on selected filters
    st.subheader("2. Cost per route");
    cost_query = build_routecost_query()

    cost_data = fetch_data(cost_query)
    st.dataframe(cost_data, width = 600 )

  elif analytical_selection == " 4. Cancellation Analysis":
    st.header("Cancellation Analysis")
    
    # Build shipment query safely based on selected filters
    st.subheader("1. Cancellation rate by origin");
    cost_query = build_cancellation_origin_query()

    cost_data = fetch_data(cost_query)
    st.dataframe(cost_data, width = 700 )
    
    # Build shipment query safely based on selected filters
    st.subheader("2. Cancellation rate by courier");
    cost_query = build_cancellation_courier_query()

    cost_data = fetch_data(cost_query)
    st.dataframe(cost_data, width = 700 )
    
  elif analytical_selection == " 5. Warehouse Insights":
    st.header("Warehouse Insights")
    
    # Build shipment query safely based on selected filters
    warehouse_query = build_warehouse_query()

    warehouse_data = fetch_data(warehouse_query)
    st.dataframe(warehouse_data, width = 700 )

