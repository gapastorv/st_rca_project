import streamlit as st
from firebase import FirebaseDB

firebase = FirebaseDB()
mail_db = st.session_state.user['email']
data = firebase.obtener_datos('db_paths', mail_db)
tables = []
print(data)
st.header('Datasets')
if data is not None:
    for key, value in zip(data.keys(), data.values()):
        nuevo_string = value.rpartition('/')[0]
        title = value.split('/')[-1]
        print(title, nuevo_string)
        table = firebase.obtener_datos(nuevo_string, title)
        print(key, table)
        st.markdown(f'## {key}')
        st.dataframe(table)
else:
    st.write('No dataset found in database, wait for mails with reports or define parsing parameters for it.')

print(tables)


