import streamlit as st
import pandas as pd
import sqlite3
import os

st.set_page_config(page_title="SmartSupply", layout="wide")
st.title("📦 SmartSupply - Inventory System")

conn = sqlite3.connect('smartsupply.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS products
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT, price REAL, stock INTEGER)''')

c.execute('''CREATE TABLE IF NOT EXISTS sales
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              product_id INTEGER, quantity INTEGER, total REAL,
              sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
conn.commit()

menu = st.sidebar.selectbox("Menu", ["Inventory", "Sales", "Analytics"])

if menu == "Inventory":
    st.header("Add Product")
    name = st.text_input("Name")
    price = st.number_input("Price", 0.0)
    stock = st.number_input("Stock", 0)
    if st.button("Add"):
        c.execute("INSERT INTO products (name,price,stock) VALUES (?,?,?)", (name,price,stock))
        conn.commit()
        st.success("Added!")
    
    st.subheader("Products")
    df = pd.read_sql("SELECT * FROM products", conn)
    st.dataframe(df)

elif menu == "Sales":
    st.header("Record Sale")
    products = pd.read_sql("SELECT * FROM products", conn)
    if not products.empty:
        prod = st.selectbox("Product", products['name'])
        qty = st.number_input("Quantity", 1)
        if st.button("Sell"):
            p = products[products['name']==prod].iloc[0]
            if p['stock'] >= qty:
                total = p['price'] * qty
                c.execute("INSERT INTO sales (product_id,quantity,total) VALUES (?,?,?)", 
                         (p['id'], qty, total))
                c.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (qty, p['id']))
                conn.commit()
                st.success("Sale recorded!")
            else:
                st.error("Insufficient stock")
    else:
        st.info("No products")

elif menu == "Analytics":
    st.header("Sales Report")
    df = pd.read_sql('''
        SELECT p.name, SUM(s.quantity) as units, SUM(s.total) as revenue
        FROM sales s JOIN products p ON s.product_id = p.id
        GROUP BY p.name
    ''', conn)
    if not df.empty:
        st.dataframe(df)
        st.metric("Total Revenue", f"₹{df['revenue'].sum():.2f}")
    else:
        st.info("No sales data")

conn.close()