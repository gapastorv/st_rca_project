import streamlit as st
from DataManager import DataManager

def print_data(data, dm):
    tabs = st.tabs(data)
    for d, s in zip(tabs,data):
        with d:
            tables = dm.get_data_by_path(s)
            for title, table in tables.items():
                st.markdown(f'## {title[1]}')
                st.dataframe(table)
                print(table)

st.header('Datasets')
dm = DataManager(st.session_state.user['uid'], st.session_state.user['email'], f'db_collection')
data = dm.get_categories()
print(data)
if not data:
    st.write('No dataframes extracted yet')
else:
    if st.button('Update', key='update'):
        data = dm.get_categories()
    print_data(data, dm)

