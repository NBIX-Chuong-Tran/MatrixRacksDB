import streamlit as st
import sqlite3
import math
import pandas as pd
import csv

# Insert to database
def __insert(rack, tube, position):
    conn = sqlite3.connect('MatrixRacksInventory.db')
    cur = conn.cursor()
    st.write("INSERT INTO Inventory (Rack, Tube, Position) VALUES (?,?,?)",(rack, tube, position))
    cur.execute("INSERT INTO Inventory (Rack, Tube, Position) VALUES (?,?,?)",(rack, tube, position))
    conn.commit()
    conn.close()

# Method to convert 1,2,3,4,5,6,7,8 to A,B,C,D,E,F,G,H
def __NumberToLetter(number):
    match number:
        case 1:
            return "A"
        case 2:
            return "B"
        case 3:
            return "C"
        case 4:
            return "D"
        case 5:
            return "E"
        case 6:
            return "F"
        case 7:
            return "G"
        case 8:
            return "H"

    return ""

# Method to convert well id in numeric (row major) to alpha-numeric
def __NumericToAlphaNumeric(number):
    alpha = __NumberToLetter(math.ceil(number/12))
    while number>12:
        number-=12
    numeric = str(number)
    return alpha+numeric

def Tube(df):
    st.metric("Rack",df['Rack'][0])
    st.metric("Tube",df['Tube'][0])
    st.metric("Position",df['Position'][0])
    st.sidebar.image("./MatrixTube.png")

def Rack(df):
    well_id = 1
    alpha_numeric_well_id = ""
    for row in range(9):
        cols = st.columns(13, vertical_alignment= "center")
        if row == 0:
            for col in range(13):
                if col == 0:
                    cols[col].text(" ")
                else:
                    cols[col].text(col)
        else:
            for col in range(13):
                if col == 0:
                    cols[col].text(__NumberToLetter(row))
                else:
                    alpha_numeric_well_id = __NumericToAlphaNumeric(well_id)
                    if alpha_numeric_well_id in df['Position'].values.tolist():
                        index = df['Position'].values.tolist().index(alpha_numeric_well_id)
                        cols[col].button(label = 'O', disabled = False, help = df['Tube'][index], key = df['Tube'][index])
                    else:
                        cols[col].button(label = "X", disabled = True, key = f'{alpha_numeric_well_id}')
                    well_id+=1
    
    st.table(df.drop("Rack", axis = 1))
    st.sidebar.image("./MatrixRack.png")


def main():
    # st.session_state

    search = False
    upload = False
    rack = False
    tube = False

    if 'df' not in st.session_state:
        st.session_state['df'] = pd.DataFrame()

    if 'df_worklist' not in st.session_state:
        st.session_state['df_worklist'] = pd.DataFrame()
    
    st.title("Matrix Racks Inventory")
    radio = st.sidebar.radio("Choose!",["General Search","Worklist"])

    if radio == "General Search":

        form = st.sidebar.form("Search for barcode",clear_on_submit=True)
        query_barcode = form.text_input(label = "Enter in rack or tube barcode", key = 'search')
        search = form.form_submit_button("Search")
    
        form2 = st.sidebar.form("Upload file to update inventory", clear_on_submit=True)
        update_file = form2.file_uploader("Choose file to upload in csv format", key = 'upload', type = 'csv')
        upload = form2.form_submit_button("Upload")

    if radio == "Worklist":
        if st.button("Clear worklist"):
            st.session_state['df_worklist'] = pd.DataFrame()
        if not st.session_state['df_worklist'].empty:
            df_delete_buttons = pd.DataFrame([False]*len(st.session_state['df_worklist']), columns = ["Delete"])
            df_delete_buttons = st.data_editor(st.session_state['df_worklist'].join(df_delete_buttons, how = 'outer'), disabled = ["Rack","Tube","Position"])
            samples_in_worklist = len(st.session_state['df_worklist'])

            st.session_state['df_worklist'] = pd.DataFrame(['Rack','Tube','Position'])
            # st.write(df_delete_buttons.drop('Delete', axis = 1))
            for index in range(samples_in_worklist):
                if df_delete_buttons['Delete'][index] == False:
                    # st.session_state['df_worklist']
                    st.write(df_delete_buttons[index])
                    st.session_state['df_worklist'] = pd.concat([st.session_state['df_worklist'],df_delete_buttons.iloc[index].drop('Delete')])
            # st.write(df_delete_buttons)
            # st.write(st.session_state['df_worklist'])
                    
        else:
            st.write("No sample in worklist")
        

    conn = sqlite3.connect('MatrixRacksInventory.db')
    
    
    ## Search
    if search:
        
        st.subheader("Searched barcode: " + query_barcode)      
        
        df = pd.read_sql_query('SELECT * FROM Inventory WHERE Rack = "'+query_barcode+'"',conn)
        if not df.empty:
            rack = True
        else:
            df = pd.read_sql_query('SELECT * FROM Inventory WHERE Tube = "'+query_barcode+'"',conn)
            if not df.empty:
                tube = True

        st.session_state['df'] = df
    
        if df.empty:
            st.subheader("No barcode found!")
        
    ## Update
    if upload:
        
        df = pd.read_sql_query('SELECT * FROM Inventory', conn)
        df_update = pd.read_csv(update_file)
        for pos in range(len(df_update)):
            if df_update['Tube'][pos] not in df['Tube'].values.tolist() and df_update['Rack'][pos] not in df['Rack'].values.tolist():
                __insert(df_update['Rack'][pos],df_update['Tube'][pos],df_update['Position'][pos])
            else:
                st.write("Failed to insert line",pos+1)
   
    # st.session_state
    for k in st.session_state.keys():
        if not isinstance(st.session_state[k],pd.DataFrame):
            if st.session_state[k] == True:
                df_temp = pd.read_sql_query('SELECT * FROM Inventory WHERE Tube = "'+k+'"',conn)
                if not df_temp.empty:
                    tube = True
                    st.session_state['df'] = df_temp
                    break

    if tube or rack:
        st.button("Add to worklist", key = 'add')

    if rack:
        Rack(st.session_state['df'])
    
    if tube:
        Tube(st.session_state['df'])

    if 'add' in st.session_state.keys():
        if st.session_state['add']:
            if st.session_state['df_worklist'].empty:
                st.session_state['df_worklist'] = pd.DataFrame(columns = st.session_state['df'].columns)
            
            st.session_state['df_worklist'] = st.session_state['df_worklist'].merge(st.session_state['df'], how = 'outer')
            st.data_editor(st.session_state['df_worklist'])
        
    conn.close()

if __name__ == "__main__":
    main()

