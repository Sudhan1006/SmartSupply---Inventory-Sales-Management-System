import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="SmartSupply", layout="wide")
st.title("📦 SmartSupply")

# Initialize DB
conn = sqlite3.connect("data.db", check_same_thread=False)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price REAL, stock INTEGER)")
c.execute("CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, product_id INTEGER, quantity INTEGER, total REAL)")
conn.commit()

menu = st.sidebar.radio("Menu", ["Products", "Sales", "Reports"])

if menu == "Products":
    st.header("Products")
    
    with st.form("add_product"):
        name = st.text_input("Product Name")
        price = st.number_input("Price", 0.0)
        stock = st.number_input("Stock", 0)
        if st.form_submit_button("Add"):
            c.execute("INSERT INTO products (name, price, stock) VALUES (?,?,?)", (name, price, stock))
            conn.commit()
            st.success("Added!")
            st.rerun()
    
    df = pd.read_sql("SELECT * FROM products", conn)
    st.dataframe(df, use_container_width=True)

elif menu == "Sales":
    st.header("Sales")
    
    products = pd.read_sql("SELECT * FROM products", conn)
    if len(products) > 0:
        prod = st.selectbox("Product", products["name"])
        qty = st.number_input("Quantity", 1)
        
        if st.button("Sell"):
            p = products[products["name"] == prod].iloc[0]
            if p["stock"] >= qty:
                total = p["price"] * qty
                c.execute("INSERT INTO sales (product_id, quantity, total) VALUES (?,?,?)", 
                         (p["id"], qty, total))
                c.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (qty, p["id"]))
                conn.commit()
                st.success(f"Sold {qty} units for ₹{total}")
                st.rerun()
            else:
                st.error("Insufficient stock")
    else:
        st.info("Add products first")

elif menu == "Reports":
    st.header("Reports")
    
    df = pd.read_sql("""
        SELECT p.name, SUM(s.quantity) as qty, SUM(s.total) as revenue
        FROM sales s
        JOIN products p ON s.product_id = p.id
        GROUP BY p.name
    """, conn)
    
    if len(df) > 0:
        st.metric("Total Revenue", f"₹{df['revenue'].sum():.2f}")
        st.dataframe(df)
        st.bar_chart(df.set_index("name")["revenue"])
    else:
        st.info("No sales yet")
