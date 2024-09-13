import streamlit as st
import sqlite3
import math
import pandas as pd
import csv

placeholder = st.empty()

# Replace the placeholder with some text:
placeholder.text("Hello")

# Replace the text with a chart:
placeholder.line_chart({"data": [1, 5, 2, 6]})

# Replace the chart with several elements:
with placeholder.container():
    st.write("This is one element")
    st.write("This is another")

# Clear all those elements:
placeholder.empty()


def __insert(rack, tube, position):
    conn = sqlite3.connect('MatrixRacksInventory.db')
    cur = conn.cursor()
    cur.execute("INSERT INTO Inventory (rack, tube, position) VALUES (?,?,?)",(rack, tube, position))
    conn.commit()
    conn.close()

st.title("Matrix Racks Inventory")

st.sidebar.title("")
st.sidebar.markdown("Search for barcodes")
query_barcode = st.sidebar.text_input("")
search = st.sidebar.button("Search")

st.sidebar.text("")
st.sidebar.markdown("Update inventory")
update_file = st.sidebar.file_uploader("Choose file to upload in csv format",type = ['csv'])
update = st.sidebar.button("Upload")

conn = sqlite3.connect('MatrixRacksInventory.db')
cur = conn.cursor()

rack = False
tube = False

placeholder = st.empty()
placeholder_sidebar = st.sidebar.empty()

## Search
if search or query_barcode:
    placeholder.empty()
    placeholder_sidebar.empty()
    df = pd.read_sql_query('SELECT * FROM Inventory WHERE Rack = "'+query_barcode+'"',conn)
    if not df.empty:
        rack = True
    else:
        df = pd.read_sql_query('SELECT * FROM Inventory WHERE Tube = "'+query_barcode+'"',conn)
        if not df.empty:
            tube = True
   
    if df.empty:
        placeholder.text("No barcode found")
    else:
        df.set_index('Position',inplace=True)
        
        
        if rack:
            placeholder_sidebar.image("./MatrixRack.png")
            ones = []
            for pos in range(len(df)):
                ones.append(1)
            df['ones'] = ones

            placeholder.table(df.drop(['ones'],axis=1))

        if tube:
            placeholder_sidebar.image("./MatrixTube.png")
            cols = placeholder.columns(3)
            cols[0].metric("Rack",df['Rack'][0])
            cols[1].metric("Tube",df['Tube'][0])
            cols[2].metric("Position",df.index[0])

## Update
if update:
    placeholder.empty()
    placeholder_sidebar.empty()
    df = pd.read_sql_query('SELECT * FROM Inventory', conn)
    placeholder.table(df)
    
    df_update = pd.read_csv(update_file)
    placeholder.table(df_update)

    for pos in range(len(df_update)): 
        if df_update['Tube'][pos] not in df['Tube'].values.tolist() and df_update['Position'][pos] not in df['Position'].values.tolist():
            __insert(df_update['Rack'][pos],df_update['Tube'][pos],df_update['Position'][pos])


conn.close()

