from firebase_admin import firestore, credentials, auth
import firebase_admin
from Hash import Hash
from pyisemail import is_email
import re

if not firebase_admin._apps:
    cred = credentials.Certificate(r"firebase_key.json")
    app = firebase_admin.initialize_app(cred, {})

    # app=firebase_admin.initialize_app()
    # print(app)


class FirebaseDB:
    def __init__(self):
        #self.USER_PATH = 'db_accounts'
        self.db = firestore.client()

    def get_db(self):
        return self.db

    def save_dataframe(self, dataframe, collection_name, path):
        # Split the path into mail and subject
        mail, subject = path.split("/")

        # Get the collection reference for mail
        mail_collection_ref = self.db.collection(collection_name).document(mail).collection(subject)

        # Convert the dataframe to a dictionary
        for title, table in dataframe:
            table_dict = table.to_dict(orient='list')
            table_reference = mail_collection_ref.document(title)
            data_path = table_reference.get().to_dict()
            if data_path is not None:
                for atribute in data_path.keys():
                    current_subjects = table_reference.get().to_dict().get(atribute, [])
                    key = ""
                    for element in table_dict.keys():
                        if element.replace(" ", "") == atribute.replace(" ", ""):
                            key = element
                    table_atribute = table_dict[key] if key != "" else []  # Agregar el nuevo valor a la lista
                    current_subjects = current_subjects + table_atribute
                    # Actualizar el valor de 'subjects' en el documento
                    table_reference.set({atribute: current_subjects}, merge=True)
            else:
                table_reference.set(table_dict, merge=True)

        print(f"Data saved to Firebase successfully. For: {mail} in the subject case: {subject}")

    def get_data(self, nombre_coleccion, nombre_documento):
        # Obtener todos los documentos de la colección
        if len(nombre_documento.split('/')) == 1:
            documentos = self.db.collection(nombre_coleccion)
            collect = documentos.document(nombre_documento)
            doc = collect.collections()
            if doc is not None:
                results = []
                for collection in doc:
                    print(f'Document data: {collection.id}')
                    results.append(collection.id)
                return results
            else:
                print(u'No such document!')
                return None
        else:
            document_id, collection_id = nombre_documento.split('/')
            documentos = self.db.collection(nombre_coleccion).document(document_id)
            collections = documentos.collection(collection_id).get()
            new_ids = []
            if collections is not None:
                for collection in collections:
                    new_ids.append(collection.id)
                print(document_id)
                return new_ids
            else:
                print(u'No such collection!')
                return None

    def add_coordinates(self, dataframe, collection_name, subject, content_type, doc_type):
        mail, subject = subject.split("/")
        json_data = dataframe.to_dict(orient='records')

        collection = self.db.collection(collection_name).document(mail).collection(doc_type)
        # subject_doc = collection.document(subject)

        for data in json_data:
            coord_doc = collection.document(subject).collection(content_type).document()
            coord_doc.set(data)

        return len(json_data)

    def extract_data(self, path, field_type, function):
        # Create a reference to the collection at the given path
        if function == 'coord':
            subject, field = field_type.split('/')
            collection_ref = self.db.collection(path).document(subject).collection(field)
            # Get all the documents within the collection
            documents = collection_ref.get()

            # Create an empty list to store the extracted data
            data_list = []

            # Iterate over each document and extract the data
            for document in documents:
                data = document.to_dict()
                data_list.append(data)

            return data_list
        elif function == 'credentials':
            collection_ref = self.db.collection(path).get()
            data_list = []
            for document in collection_ref:
                data = document.to_dict()
                data_list.append(data)

            return data_list
        else:
            collection_ref = self.db.collection(path).document(field_type)
            # Get all the documents within the collection
            document = collection_ref.get().to_dict()
            return field_type, document

    def get_names_in_path(self, doc_path):
        doc_ref = self.db.document(doc_path)
        collections = doc_ref.collections()
        collection_names = [collection.id for collection in collections]
        return collection_names

    def signup(self, mail, password, name):
        try:
            matcher = re.match('^[_a-zA-Z0-9-]+(\.[_a-zA-Z0-9-]+)*@(gmail|outlook|hotmail)\.com$', mail)
            if matcher is not None:
                bool_result = is_email(mail, check_dns=True)
                print(bool_result)
                user = auth.create_user(email=mail, password=password, display_name=name)
                collection = self.db.collection('db_acc').document(user.uid)
                data = {
                    'mail': Hash.e_s_f(mail),
                    'pass': Hash.h_dm5(password),
                    'mailk': '',
                    'username': Hash.e_s_f(name),
                    'access': False,
                    'subjects': {}
                }
                collection.set(data)
                return user, 0
            else:
                return None, -1
        except auth.EmailAlreadyExistsError:
            return None, 1
        except auth.UidAlreadyExistsError:
            return None, 2
        except auth.UnexpectedResponseError:
            return None, 3

    def set_user_data(self, uid, field, val):
        try:
            collection = self.db.collection('db_acc').document(uid)
            if field == 'subjects':
                # Obtener la lista actual de 'subjects' en el documento
                current_subjects = collection.get().to_dict().get('subjects', {})
                # Agregar el nuevo valor a la lista
                for key, value in val.items():
                    current_subjects[key] = value
                # Actualizar el valor de 'subjects' en el documento
                collection.set({'subjects': current_subjects}, merge=True)
            else:
                collection.set({field: Hash.e_s_f(val) if not isinstance(val, bool) else val}, merge=True)
            return 0
        except auth.UnexpectedResponseError:
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
                if Hash.h_dm5(password) == values['pass']:
                    user_info['nombre'] = Hash.d_s_f(values['username'])
                    print(user_info)
                    return user_info, 0
                else:
                    return user_info, -1
        except auth.UserNotFoundError:
            # Manejar errores de autenticación, por ejemplo, credenciales incorrectas
            return None, 1
        except auth.UnexpectedResponseError:
            # Manejar errores inesperados
            return None, 2

# firebase = FirebaseDB()
# value = firebase.set_user_data('ovk5Bjt2Lin5rlIzgcIx', 'subjects', {'AT':'Tested'})
# dataframe = firebase.extract_data("db_coord/test/coord")
# print(dataframe)
