import pandas as pd
import json
from firebase_admin import firestore
import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate(r"firebase_key.json")
firebase_admin.initialize_app(cred)

class FirebaseDB:
    def __init__(self):
        self.db = firestore.client()

    def guardar_dataframe(self, dataframe, collection_name, path, file_name):
        # Split the path into mail and subject
        mail, subject = path.split("/")

        # Get the collection reference for mail
        mail_collection_ref = self.db.collection(collection_name).document(mail).collection(subject)

        # Convert the dataframe to a dictionary
        for data in dataframe:
            datos_json = data.to_dict(orient='list')

            # Create a new document in the mail_collection_ref for each dataframe
            doc_ref = (mail_collection_ref.document(file_name).
                       collection('table').document())
            doc_ref.set(datos_json)

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
        #subject_doc = collection.document(subject)

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

        # Create a dataframe from the extracted data
        dataframe = pd.concat([pd.DataFrame(data, index=[0]) for data in data_list], ignore_index=True)

        return data_list


#firebase = FirebaseDB()
#dataframe = firebase.extract_data("db_coord/test/coord")
#print(dataframe)
