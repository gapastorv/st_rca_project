import streamlit as st
from firebase import FirebaseDB


def get_categories():
    firebase = FirebaseDB()
    mail_db = st.session_state.user['email']
    data = firebase.obtener_datos('db_collection', mail_db)
    return data


def get_data(data):
    firebase = FirebaseDB()
    mail_db = st.session_state.user['email']
    table_info = []
    print(data)
    tabs = st.tabs(data)
    for d, s in zip(tabs, data):
        with d:
            values = firebase.obtener_datos(f'db_collection', f'{mail_db}/{s}')
            print(s)
            for v in values:
                title, table = firebase.extract_data(f'db_collection/{mail_db}/{s}', v, 'tables')
                st.markdown(f'## {title}')
                st.dataframe(table)
                print(title)
                table_info.append((s, title, table))
    # print(table_info)
    return table_info


st.header('Datasets')
data = get_categories()
print(data)
if not data:
    st.write('No dataframes extracted yet')
else:
    if st.button('Update', key='update'):
        data = get_categories()
    get_data(data)

