import json
import pandas as pd
from firebase_admin import firestore, credentials, auth, db
import firebase_admin
import os
import hash

if not firebase_admin._apps:
    cred = credentials.Certificate(r"firebase_key.json")
    app = firebase_admin.initialize_app(cred, {})

    # app=firebase_admin.initialize_app()
    # print(app)


class FirebaseDB:
    def __init__(self):
        self.USER_PATH = 'db_accounts'
        self.db = firestore.client()

    def guardar_dataframe(self, dataframe, collection_name, saved_path, path, file_name):
        # Split the path into mail and subject
        mail, subject = path.split("/")

        # Get the collection reference for mail
        mail_collection_ref = self.db.collection(collection_name).document(mail).collection(subject)

        path_collection_ref = self.db.collection(saved_path).document(mail)

        # Convert the dataframe to a dictionary
        for title, table in dataframe:
            table_dict = table.to_dict(orient='list')

            # Create a new document in the mail_collection_ref for each dataframe
            table_ref = mail_collection_ref.document(file_name).collection('table')
            doc_ref = table_ref.document(title)
            doc_ref.set(table_dict)
            path = collection_name + "/" + mail + "/" + subject + "/" + file_name + "/table/" + title
            path_collection_ref.set({
                title+"-"+file_name: path
            }, merge=True)

        print("Data saved to Firebase successfully.")

    def obtener_datos(self, nombre_coleccion, nombre_documento):
        # Obtener todos los documentos de la colección
        documentos = self.db.collection(nombre_coleccion)
        collect = documentos.document(nombre_documento)
        doc = collect.get()
        if doc.exists:
            result = doc.to_dict()
            print(f'Document data: {doc.to_dict()}')
            return result
        else:
            print(u'No such document!')
            return None

    def add_coordinates(self, dataframe, collection_name, subject, type):
        mail, subject = subject.split("/")
        json_data = dataframe.to_dict(orient='records')

        collection = self.db.collection(collection_name).document(mail).collection(subject)
        # subject_doc = collection.document(subject)

        for data in json_data:
            coord_doc = collection.document(type).collection('coord').document()
            coord_doc.set(data)

        return len(json_data)

    def extract_data(self, path, field_type, function):
        # Create a reference to the collection at the given path
        if function == 'coord':
            collection_ref = self.db.collection(path).document(field_type).collection('coord')
        else:
            collection_ref = self.db.collection(path)

        # Get all the documents within the collection
        documents = collection_ref.get()

        # Create an empty list to store the extracted data
        data_list = []

        # Iterate over each document and extract the data
        for document in documents:
            data = document.to_dict()
            data_list.append(data)

        return data_list

    def get_names_in_path(self, doc_path):
        doc_ref = self.db.document(doc_path)
        subcollections = doc_ref.collections()
        subcollection_names = [subcollection.id for subcollection in subcollections]
        return subcollection_names

    def signup(self, mail, password, name):
        try:
            user = auth.create_user(email=mail, password=password, display_name=name)
            collection = self.db.collection('db_acc').document(user.uid)
            data = {
                'mail': hash.e_s_f(mail),
                'pass': hash.h_dm5(password),
                'mailk': '',
                'username': hash.e_s_f(name),
                'access': False,
                'subjects': []
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
            if field == 'subjects':
                # Obtener la lista actual de 'subjects' en el documento
                current_subjects = collection.get().get('subjects', [])
                # Agregar el nuevo valor a la lista
                current_subjects.append(value)
                # Actualizar el valor de 'subjects' en el documento
                collection.set({'subjects': current_subjects}, merge=True)
            else:
                collection.set({field: hash.e_s_f(value) if not isinstance(value, bool) else value}, merge=True)
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
                    'imap': False if values['mailk'] == '' else True
                }
                if hash.h_dm5(password) == values['pass']:
                    user_info['nombre'] = hash.d_s_f(values['username'])
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

