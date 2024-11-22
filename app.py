import streamlit as st
import sqlite3
import math
import pandas as pd

##
## sql code to create tables

# CREATE TABLE IF NOT EXISTS Tube (
# ID INTEGER PRIMARY KEY,
# Barcode TEXT unique,
# Position TEXT,
# Rack_ID INTEGER,
# UNIQUE (Position, Rack_ID)
# );

# CREATE TABLE IF NOT EXISTS Rack (
# ID INTEGER PRIMARY KEY,
# Barcode TEXT UNIQUE,
# Position TEXT,
# Tray_ID Integer,
# UNIQUE (Position, Tray_ID)
# );

# CREATE TABLE IF NOT EXISTS Tray (
# ID INTEGER PRIMARY KEY,
# Barcode TEXT,
# Position TEXT,
# Location_ID INTEGER,
# UNIQUE (Position, Location_ID)
# );

# CREATE TABLE IF NOT EXISTS Location (
# ID Integer PRIMARY KEY,
# Name TEXT UNIQUE
# )


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

    ## Tube
    cols_tube = st.columns(2)
    cols_tube[0].metric("Barcode",df['Tube Barcode'][0])
    cols_tube[1].metric("Position",df['Tube Position'][0])

    ## Rack
    cols_rack = st.columns(2)
    cols_rack[0].metric("Rack",df['Rack Barcode'][0])
    cols_rack[1].metric("Position",df['Rack Position'][0])
    
    ## Tray
    cols_tray = st.columns(2)
    cols_tray[0].metric("Tray",df['Tray Barcode'][0])
    cols_tray[1].metric("Position",df['Tray Position'][0])

    ## Location
    cols_location = st.columns(2)
    cols_location[0].metric("Location",df['Location'][0])

    ## Sidebar image
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

def Tube_Barcodes(barcode):
    conn = sqlite3.connect('MatrixRacksInventory.db')
    df = pd.read_sql_query('SELECT * FROM Tube WHERE Barcode = "'+barcode+'" LIMIT 1',conn)

    if not df.empty:

        df = df.rename(columns = {"Barcode":"Tube Barcode", "Position":"Tube Position"})
        
        df_rack = pd.read_sql_query('SELECT * FROM Rack WHERE ID = '+str(df['Rack_ID'][0])+' LIMIT 1',conn)
        df = df.drop(columns = ['ID','Rack_ID'],axis=1)
        df_rack = df_rack.rename(columns = {"Barcode":"Rack Barcode","Position":"Rack Position"})

        df_tray = pd.read_sql_query('SELECT * FROM Tray WHERE ID = '+str(df_rack['Tray_ID'][0])+' LIMIT 1',conn)
        df_rack = df_rack.drop(columns=['ID','Tray_ID'],axis=1)
        df_tray = df_tray.rename(columns = {"Barcode":"Tray Barcode","Position":"Tray Position"})

        df_location = pd.read_sql_query('SELECT * FROM Location WHERE ID = '+str(df_tray['Location_ID'][0])+' LIMIT 1',conn)
        df_tray = df_tray.drop(columns=['ID','Location_ID'],axis=1)
        df_location = df_location.drop(columns=['ID'],axis=1)
        df_location = df_location.rename(columns = {"Name":"Location"})

        df = pd.concat([df,df_rack,df_tray,df_location],axis=1)
    
    return df

def Add_to_Worklist(df):
    if st.session_state['df_worklist'].empty:
        st.session_state['df_worklist'] = pd.DataFrame(columns = df.columns)
    
    st.session_state['df_worklist'] = st.session_state['df_worklist'].merge(df, how = 'outer')

def main():
    # st.session_state

    search = False
    upload = False
    search_and_add = False

    tube = False
    rack = False
    tray = False
    location = False

    if 'df' not in st.session_state:
        st.session_state['df'] = pd.DataFrame()

    if 'df_worklist' not in st.session_state:
        st.session_state['df_worklist'] = pd.DataFrame()
    
    st.title("Matrix Racks Inventory")
    radio = st.sidebar.radio("Choose!",["General Search","Worklist","All Inventory"])

    if radio == "General Search":

        form = st.sidebar.form("Search for barcode",clear_on_submit=True)
        query_barcode = form.text_input(label = "Enter in rack or tube barcode", key = 'search')
        search = form.form_submit_button("Search")
    
        form2 = st.sidebar.form("Upload file to update inventory", clear_on_submit=True)
        update_file = form2.file_uploader("Choose file to upload in csv format", key = 'upload', type = 'csv')
        upload = form2.form_submit_button("Upload")

    if radio == "Worklist":
        
        form = st.sidebar.form("Type in list of barcodes to add to worklist (each separated by new line)", clear_on_submit = True)
        worklist_barcodes = form.text_area(label = "All tube barcodes needed to be added to the worklist (separated by space or new line)", key = 'add_to_worklist')
        search_and_add = form.form_submit_button("Seach and add to worklist")

        if st.button("Clear worklist"):
            st.session_state['df_worklist'] = pd.DataFrame()
        
    conn = sqlite3.connect('MatrixRacksInventory.db')
    cur = conn.cursor()
    
    ## Search
    if search:
        st.session_state['df'] = Tube_Barcodes(query_barcode) 
        if st.session_state['df'].empty:
            st.subheader(query_barcode + " not found!")
        else:
            tube = True
    
    ## Upload
    if upload:

        df_result = pd.DataFrame(columns = ['Tube','Rack','Tray','Location'])
        
        df_tube = pd.read_sql_query('SELECT * FROM Tube', conn)
        df_rack = pd.read_sql_query('SELECT * FROM Rack',conn)
        df_tray = pd.read_sql_query('SELECT * FROM Tray',conn)
        df_location = pd.read_sql_query('SELECT * FROM Location',conn)
        df_update = pd.read_csv(update_file, dtype = str)
        df_issue = pd.DataFrame(columns = df_update.columns.tolist().append('Error'))
        df_error = pd.DataFrame(columns = ['Error'])
        errors = 0

        result_cols = st.columns(2)
        result_cols[0] = st.empty()
        result_cols[1] = st.empty()

        with st.spinner():

            result_cols = st.columns(2)
            result_cols[0] = st.empty()
            result_cols[1] = st.empty()

            for pos in range(len(df_update)):
                
                ## Add location
                location_existed = False
                cur.execute('''SELECT * FROM Location WHERE Name = ?''',(df_update['Location'][pos],))
                location_db = cur.fetchone()

                if location_db:
                    location_existed = True
                    df_result.at['Line '+str(pos+1),'Location'] = 'Existed'

                if not location_existed:
                    cur.execute('''INSERT INTO Location (Name) VALUES (?)''',(df_update['Location'][pos],))
                    conn.commit()
                    df_result.at['Line '+str(pos+1),'Location'] = 'Added'
                
                ## Add tray
                cur.execute('''SELECT ID FROM Location WHERE Name = ? ''',(df_update['Location'][pos],))
                location_id = cur.fetchone()[0]

                tray_existed = False
                tray_position_and_location = False

                tray_db = []
                if not location_id == 1:
                    cur.execute('''SELECT * FROM Tray WHERE Position = ? AND Location_ID = ? ''', (df_update['Tray Position'][pos],location_id,))
                    tray_db = cur.fetchone()
                else:
                    df_update.at[pos,'Tray Position'] = None


                if tray_db:
                    tray_position_and_location = True
                    if df_update['Tray Barcode'][pos] in tray_db:
                        tray_existed = True
                else:
                    cur.execute('''SELECT * FROM Tray WHERE Barcode = ?''',(df_update['Tray Barcode'][pos],))
                    tray_db = cur.fetchone()
                    if tray_db:
                        tray_existed = True

          
                if tray_existed and tray_position_and_location:
                    df_result.at['Line '+str(pos+1),'Tray'] = 'Existed'
                if tray_existed and not tray_position_and_location:
                    df_result.at['Line '+str(pos+1),'Tray'] = 'Update'
                    cur.execute('''UPDATE Tray SET Position = ?, Location_ID = ? WHERE Barcode = ? ''',(df_update['Tray Position'][pos], location_id, df_update['Tray Barcode'][pos],))
                if not tray_existed and not tray_position_and_location:
                    df_result.at['Line '+str(pos+1),'Tray'] = 'Insert'
                    cur.execute('''INSERT INTO Tray (Position, Location_ID, Barcode) VALUES (?,?,?) ''',(df_update['Tray Position'][pos], location_id, df_update['Tray Barcode'][pos],))
                if not tray_existed and tray_position_and_location:
                    df_result.at['Line '+str(pos+1),'Tray'] = 'Error'
                    df_result.at['Line '+str(pos+1),'Rack'] = 'Skipped'
                    df_result.at['Line '+str(pos+1),'Tube'] = 'Skipped'

                conn.commit()


                ## Add rack
                if not df_result.at['Line '+str(pos+1),'Rack'] == 'Skipped':
                    cur.execute('''SELECT ID FROM Tray WHERE Barcode = ?''',(df_update['Tray Barcode'][pos],))
                    tray_id = cur.fetchone()[0]

                    rack_existed = False
                    rack_position_and_tray = False

                    rack_db = []
                    if not tray_id == 1:
                        cur.execute('''SELECT * FROM Rack WHERE Position = ? AND Tray_ID = ? ''', (df_update['Rack Position'][pos],tray_id,))
                        rack_db = cur.fetchone()
                    else:
                        df_update.at[pos,'Rack Position'] = None

                    if rack_db:
                        rack_position_and_tray = True
                        if df_update['Rack Barcode'][pos] in rack_db:
                            rack_existed = True
                    else:
                        cur.execute('''SELECT * FROM Rack WHERE Barcode = ?''',(df_update['Rack Barcode'][pos],))
                        rack_db = cur.fetchone()
                        if rack_db:
                            rack_existed = True

                    
                    if rack_existed and rack_position_and_tray:
                        df_result.at['Line '+str(pos+1),'Rack'] = 'Existed'
                    if rack_existed and not rack_position_and_tray:
                        df_result.at['Line '+str(pos+1),'Rack'] = 'Update'
                        cur.execute('''UPDATE Rack SET Position = ?, Tray_ID = ? WHERE Barcode = ? ''',(df_update['Rack Position'][pos], tray_id, df_update['Rack Barcode'][pos],))
                    if not rack_existed and not rack_position_and_tray:
                        df_result.at['Line '+str(pos+1),'Rack'] = 'Insert'
                        cur.execute('''INSERT INTO Rack (Position, Tray_ID, Barcode) VALUES (?,?,?) ''',(df_update['Rack Position'][pos], tray_id, df_update['Rack Barcode'][pos],))
                    if not rack_existed and rack_position_and_tray:
                        df_result.at['Line '+str(pos+1),'Rack'] = 'Error'
                        df_result.at['Line '+str(pos+1),'Tube'] = 'Skipped'
                    
                    conn.commit()
                    # df_rack = pd.read_sql_query('''SELECT * FROM Rack''',conn)

                
                ## Add tube
                if not df_result.at['Line '+str(pos+1),'Tube'] == 'Skipped':
                    cur.execute('''SELECT ID FROM Rack WHERE Barcode = ?''',(df_update['Rack Barcode'][pos],))
                    rack_id = cur.fetchone()[0]

                    tube_existed = False
                    tube_position_and_rack = False

                    tube_db = []
                    if not rack_id == 1:
                        cur.execute('''SELECT * FROM Tube WHERE Position = ? AND Rack_ID = ? ''', (df_update['Tube Position'][pos],rack_id,))
                        tube_db = cur.fetchone()
                    else:
                        df_update.at[pos,'Tube Position'] = None

                    if tube_db:
                        tube_position_and_rack = True
                        if df_update['Tube Barcode'][pos] in tube_db:
                            tube_existed = True
                    else:
                        cur.execute('''SELECT * FROM Tube WHERE Barcode = ?''',(df_update['Tube Barcode'][pos],))
                        tube_db = cur.fetchone()
                        if tube_db:
                            tube_existed = True

    
                    if tube_existed and tube_position_and_rack:
                        df_result.at['Line '+str(pos+1),'Tube'] = 'Existed'
                    if tube_existed and not tube_position_and_rack:
                        df_result.at['Line '+str(pos+1),'Tube'] = 'Update'
                        cur.execute('''UPDATE Tube SET Position = ?, Rack_ID = ? WHERE Barcode = ? ''',(df_update['Tube Position'][pos], rack_id, df_update['Tube Barcode'][pos],))
                    if not tube_existed and not tube_position_and_rack:
                        df_result.at['Line '+str(pos+1),'Tube'] = 'Insert'
                        cur.execute('''INSERT INTO Tube (Position, Rack_ID, Barcode) VALUES (?,?,?) ''',(df_update['Tube Position'][pos], rack_id, df_update['Tube Barcode'][pos],))
                    if not tube_existed and tube_position_and_rack:
                        df_result.at['Line '+str(pos+1),'Tube'] = 'Error'

                    conn.commit()
                
                if  df_result['Tray']['Line '+str(pos+1)] == 'Error' or df_result['Rack']['Line '+str(pos+1)] == 'Error' or df_result['Tube']['Line '+str(pos+1)] == 'Error':
                    df_issue = pd.concat([df_issue,df_update.loc[[pos]]], ignore_index= True)
                    if df_result['Tray']['Line '+str(pos+1)] == 'Error':
                        df_issue.at[errors,'Error'] = 'Tray'
                    if df_result['Rack']['Line '+str(pos+1)] == 'Error':
                        df_issue.at[errors,'Error'] = 'Rack'
                    if df_result['Tube']['Line '+str(pos+1)] == 'Error':
                        df_issue.at[errors,'Error'] = 'Tube'
                    errors+=1
      
                with result_cols[0]:
                    st.dataframe(df_result)
                with result_cols[1]:
                    st.dataframe(df_issue)

    ## Search and add to worklist       
    if search_and_add:
        barcodes = worklist_barcodes.split()
        for barcode in barcodes:
            df = Tube_Barcodes(barcode)
            if df.empty:
                st.write(barcode + " not found")
            else:
                Add_to_Worklist(df)

    ## Display tube info
    if tube:
        st.button("Add to worklist", key = 'add')
        Tube(st.session_state['df'])

    ## Display rack info
    if rack:
        Rack(st.session_state['df'])
    
    ## Add tube to worklist    
    if 'add' in st.session_state.keys():
        if st.session_state['add']:
            Add_to_Worklist(st.session_state['df'])
            st.dataframe(st.session_state['df_worklist'])
            
    ## Display worklist
    if not st.session_state['df_worklist'].empty and radio == "Worklist":
        st.dataframe(st.session_state['df_worklist'])
        # st.dataframe(st.session_state['df_worklist'].sort_values(['Name','Shelf','Tray Barcode','Rack Position','Rack Barcode','Tube Position']))

    if radio == "All Inventory":
        df_tube = pd.read_sql_query('SELECT * FROM Tube', conn)
        df_rack = pd.read_sql_query('SELECT * FROM Rack',conn)
        df_tray = pd.read_sql_query('SELECT * FROM Tray',conn)
        df_location = pd.read_sql_query('SELECT * FROM Location',conn)

        st.write("Tubes")
        st.dataframe(df_tube)

        st.write("Racks")
        st.dataframe(df_rack)

        st.write("Trays")
        st.dataframe(df_tray)

        st.write("Locations")
        st.dataframe(df_location)
        
    conn.close()

if __name__ == "__main__":
    main()

