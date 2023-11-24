import json
import pandas as pd
from firebase_admin import firestore, credentials, auth
import firebase_admin
import os
import hash

if not firebase_admin._apps:
    cred = credentials.Certificate(r"firebase_key.json")
    app = firebase_admin.initialize_app(cred)

    # app=firebase_admin.initialize_app()
    # print(app)
class FirebaseDB:
    def __init__(self):
        self.USER_PATH = 'db_accounts'
        self.db = firestore.client()

    def guardar_dataframe(self, dataframe, collection_name, path, file_name):
        # Split the path into mail and subject
        mail, subject = path.split("/")

        # Get the collection reference for mail
        mail_collection_ref = self.db.collection(collection_name).document(mail).collection(subject)

        # Convert the dataframe to a dictionary
        for title, table in dataframe:
            table_dict = table.to_dict(orient='list')

            # Create a new document in the mail_collection_ref for each dataframe
            table_ref = mail_collection_ref.document(file_name).collection('table')
            doc_ref = table_ref.document(title)
            doc_ref.set(table_dict)

        print("Data saved to Firebase successfully.")

    def obtener_tabla(self, nombre_coleccion):
        # Obtener todos los documentos de la colección
        documentos = self.db.collection(nombre_coleccion).get()

        # Crear una lista vacía para almacenar los datos del documento
        data_list = []

        # Iterar sobre los documentos y añadirlos a la lista
        for documento in documentos:
            datos = documento.to_dict()
            data_list.append(datos)

        # Crear un dataframe a partir de los datos extraídos
        dataframe = pd.concat([pd.DataFrame(data, index=[0]) for data in data_list], ignore_index=True)

        return dataframe

    def add_coordinates(self, dataframe, collection_name, subject):
        mail, subject = subject.split("/")
        json_data = dataframe.to_dict(orient='records')

        collection = self.db.collection(collection_name).document(mail).collection(subject)
        # subject_doc = collection.document(subject)

        for data in json_data:
            coord_doc = collection.document('tables').collection('coord').document()
            coord_doc.set(data)

        return len(json_data)

    def extract_data(self, path):
        # Create a reference to the collection at the given path
        collection_ref = self.db.collection(path).document('tables').collection('coord')

        # Get all the documents within the collection
        documents = collection_ref.get()

        # Create an empty list to store the extracted data
        data_list = []

        # Iterate over each document and extract the data
        for document in documents:
            data = document.to_dict()
            data_list.append(data)

        return data_list

    def signup(self, mail, password, name):
        try:
            user = auth.create_user(email=mail, password=password, display_name=name)
            collection = self.db.collection('db_acc').document(user.uid)
            data = {
                'em': hash.e_s_f(mail),
                'ps': hash.h_dm5(password),
                'ek': '',
                'un': hash.e_s_f(name)
            }
            collection.set(data)
            return user, 0
        except auth.EmailAlreadyExistsError as e:
            return None, 1
        except auth.UidAlreadyExistsError as e:
            return None, 2
        except auth.UnexpectedResponseError as e:
            return None, 3

    def set_user_data(self, uid, field, value):
        try:
            collection = self.db.collection('db_acc').document(uid)
            collection.set({field: hash.e_s_f(value)}, merge=True)
            return 0
        except auth.UnexpectedResponseError as e:
            return 1

    def get_user(self, email, password):
        try:
            # Verificar las credenciales (email y contraseña)
            user = auth.get_user_by_email(email)
            collection = self.db.collection('db_acc').document(user.uid)
            data = collection.get()
            if data.exists:
                values = data.to_dict()
                # Obtener información del usuario
                user_info = {
                    'uid': user.uid,
                    'nombre': '',
                    'email': user.email,
                    'imap': False if values['ek'] == '' else True
                }
                if hash.h_dm5(password) == values['ps']:
                    user_info['nombre'] = hash.d_s_f(values['un'])
                    print(user_info)
                    return user_info, 0
                else:
                    return user_info, -1
        except auth.UserNotFoundError as e:
            # Manejar errores de autenticación, por ejemplo, credenciales incorrectas
            return None, 1
        except auth.UnexpectedResponseError as e:
            # Manejar errores inesperados
            return None, 2

# firebase = FirebaseDB()
# dataframe = firebase.extract_data("db_coord/test/coord")
# print(dataframe)
