# COMPLETE FIXED APP.PY - Copy this entire file
import streamlit as st
import pandas as pd
import sqlite3
import os
import tempfile

# Page config MUST be first command
st.set_page_config(
    page_title="SmartSupply",
    page_icon="📦",
    layout="wide"
)

# Title
st.title("📦 SmartSupply - Inventory System")
st.markdown("---")

# Use temporary directory for database (Streamlit Cloud fix)
db_path = os.path.join(tempfile.gettempdir(), "smartsupply.db")

try:
    # Connect to database
    conn = sqlite3.connect(db_path, check_same_thread=False)
    c = conn.cursor()
    
    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE,
                  price REAL,
                  stock INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS sales
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  product_id INTEGER,
                  quantity INTEGER,
                  total REAL,
                  date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    
    # Sidebar menu
    menu = st.sidebar.radio(
        "Navigation",
        ["📊 Dashboard", "📦 Inventory", "💰 Sales", "📈 Analytics"]
    )
    
    # DASHBOARD
    if menu == "📊 Dashboard":
        st.header("📊 Dashboard")
        
        # Get stats
        products_df = pd.read_sql("SELECT COUNT(*) as count, SUM(stock) as total_stock FROM products", conn)
        sales_df = pd.read_sql("SELECT COUNT(*) as count, SUM(total) as revenue FROM sales", conn)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Products", int(products_df['count'].iloc[0]) if not products_df.empty else 0)
        with col2:
            st.metric("Total Stock", int(products_df['total_stock'].iloc[0]) if not pd.isna(products_df['total_stock'].iloc[0]) else 0)
        with col3:
            st.metric("Sales", int(sales_df['count'].iloc[0]) if not sales_df.empty else 0)
        with col4:
            revenue = float(sales_df['revenue'].iloc[0]) if not pd.isna(sales_df['revenue'].iloc[0]) else 0
            st.metric("Revenue", f"₹{revenue:,.2f}")
        
        # Recent sales
        st.subheader("Recent Sales")
        recent = pd.read_sql("""
            SELECT p.name, s.quantity, s.total, s.date 
            FROM sales s
            JOIN products p ON s.product_id = p.id
            ORDER BY s.date DESC LIMIT 5
        """, conn)
        
        if not recent.empty:
            st.dataframe(recent, use_container_width=True)
        else:
            st.info("No sales yet")
    
    # INVENTORY
    elif menu == "📦 Inventory":
        st.header("📦 Inventory Management")
        
        tab1, tab2 = st.tabs(["➕ Add Product", "📋 View Products"])
        
        with tab1:
            with st.form("add_product"):
                name = st.text_input("Product Name")
                col1, col2 = st.columns(2)
                with col1:
                    price = st.number_input("Price (₹)", min_value=0.0, value=100.0, step=10.0)
                with col2:
                    stock = st.number_input("Stock", min_value=0, value=10, step=1)
                
                submitted = st.form_submit_button("Add Product", type="primary")
                if submitted:
                    if name:
                        try:
                            c.execute("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
                                    (name, price, stock))
                            conn.commit()
                            st.success(f"✅ {name} added successfully!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Product already exists!")
                    else:
                        st.error("Please enter product name")
        
        with tab2:
            products = pd.read_sql("SELECT * FROM products ORDER BY name", conn)
            if not products.empty:
                products['Value'] = products['price'] * products['stock']
                products['price'] = products['price'].apply(lambda x: f"₹{x:,.2f}")
                products['Value'] = products['Value'].apply(lambda x: f"₹{x:,.2f}")
                
                st.dataframe(
                    products[['name', 'price', 'stock', 'Value']],
                    column_config={
                        "name": "Product",
                        "price": "Price",
                        "stock": "Stock",
                        "Value": "Total Value"
                    },
                    use_container_width=True,
                    hide_index=True
                )
                
                total_value = sum(p[2] * p[3] for p in pd.read_sql("SELECT * FROM products", conn).values)
                st.metric("Total Inventory Value", f"₹{total_value:,.2f}")
            else:
                st.info("No products yet. Add your first product!")
    
    # SALES
    elif menu == "💰 Sales":
        st.header("💰 Sales Management")
        
        products = pd.read_sql("SELECT * FROM products WHERE stock > 0 ORDER BY name", conn)
        
        if products.empty:
            st.warning("No products available. Add products in Inventory first!")
        else:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("Record Sale")
                
                with st.form("record_sale"):
                    product_name = st.selectbox(
                        "Select Product",
                        products['name'].tolist()
                    )
                    
                    selected_product = products[products['name'] == product_name].iloc[0]
                    
                    st.info(f"Price: ₹{selected_product['price']:,.2f} | Available: {selected_product['stock']} units")
                    
                    quantity = st.number_input(
                        "Quantity",
                        min_value=1,
                        max_value=int(selected_product['stock']),
                        value=1
                    )
                    
                    total = float(selected_product['price']) * quantity
                    st.success(f"Total: ₹{total:,.2f}")
                    
                    if st.form_submit_button("💵 Record Sale", type="primary"):
                        c.execute("INSERT INTO sales (product_id, quantity, total) VALUES (?, ?, ?)",
                                (int(selected_product['id']), quantity, total))
                        c.execute("UPDATE products SET stock = stock - ? WHERE id = ?",
                                (quantity, int(selected_product['id'])))
                        conn.commit()
                        st.success(f"✅ Sale recorded: {quantity} x {product_name} = ₹{total:,.2f}")
                        st.rerun()
            
            with col2:
                st.subheader("Recent Sales")
                sales = pd.read_sql("""
                    SELECT p.name, s.quantity, s.total, s.date
                    FROM sales s
                    JOIN products p ON s.product_id = p.id
                    ORDER BY s.date DESC LIMIT 10
                """, conn)
                
                if not sales.empty:
                    sales['total'] = sales['total'].apply(lambda x: f"₹{x:,.2f}")
                    st.dataframe(sales, use_container_width=True, hide_index=True)
                    
                    total_revenue = pd.read_sql("SELECT SUM(total) as revenue FROM sales", conn).iloc[0]['revenue']
                    st.metric("Total Revenue", f"₹{total_revenue:,.2f}" if total_revenue else "₹0.00")
                else:
                    st.info("No sales yet")
    
    # ANALYTICS
    elif menu == "📈 Analytics":
        st.header("📈 Business Analytics")
        
        sales_data = pd.read_sql("""
            SELECT 
                p.name as Product,
                SUM(s.quantity) as Units_Sold,
                SUM(s.total) as Revenue
            FROM sales s
            JOIN products p ON s.product_id = p.id
            GROUP BY p.name
            ORDER BY Revenue DESC
        """, conn)
        
        if not sales_data.empty:
            col1, col2, col3 = st.columns(3)
            
            total_revenue = sales_data['Revenue'].sum()
            total_units = sales_data['Units_Sold'].sum()
            avg_price = total_revenue / total_units if total_units > 0 else 0
            
            with col1:
                st.metric("Total Revenue", f"₹{total_revenue:,.2f}")
            with col2:
                st.metric("Units Sold", f"{total_units:,.0f}")
            with col3:
                st.metric("Avg Price/Unit", f"₹{avg_price:,.2f}")
            
            st.subheader("Sales by Product")
            st.dataframe(sales_data, use_container_width=True, hide_index=True)
            
            st.subheader("Revenue Distribution")
            chart_data = sales_data.set_index('Product')['Revenue']
            st.bar_chart(chart_data)
        else:
            st.info("No sales data available yet. Record some sales first!")
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.caption("SmartSupply v1.0")
    st.sidebar.caption(f"Database: {db_path}")
    
except Exception as e:
    st.error(f"Application Error: {str(e)}")
    st.info("Please refresh the page or contact support")
    
    # Debug info
    with st.expander("Debug Information"):
        st.code(f"Error: {str(e)}")
        st.code(f"Database path: {db_path}")
        st.code(f"Python version: {os.sys.version}")
