import pandas as pd
from Firebase import FirebaseDB


class DataManager:
    def __init__(self, user_id, mail, collection_name):
        #self.user_id = user_id
        self.mail = mail
        self.collection_name = collection_name
        self.firebase = FirebaseDB()
        self.data_tables = {}

    def get_categories(self):
        data = self.firebase.get_data(self.collection_name, self.mail)
        return data

    def get_data_by_path(self, category):
        data_tables = {}
        values = self.firebase.get_data(f'{self.collection_name}',
                                             f'{self.mail}/{category}')
        print(values)
        for v in values:
            title, table = self.firebase.extract_data(f'{self.collection_name}/{self.mail}/{category}',
                                                      v, 'tables')
            data_tables[(category, title)] = table

        return data_tables

    def update_data(self):
        data = self.get_categories()
        for d in data:
            tables = self.get_data_by_path(d)
            self.data_tables.update(tables)

        return self.data_tables

    @staticmethod
    def modify_table(dataframe, column, type):
        if type == 'numeric':
            # Solo tomar las filas donde la columna específica no sea nula y sea numérica
            dataframe = dataframe.dropna(subset=[column])
            dataframe[column] = pd.to_numeric(dataframe[column], errors='coerce')
            dataframe = dataframe.dropna(subset=[column])
        elif type == 'string':
            # Eliminar filas donde todos los valores sean nulos
            dataframe = dataframe.dropna(how='all')
            dataframe[column] = dataframe[column].astype(str)
        elif type == 'date':
            # Intentar convertir a formato de fecha
            try:
                dataframe[column] = pd.to_datetime(dataframe[column], errors='coerce')
                dataframe = dataframe.dropna(subset=[column])
            except ValueError:
                pass  # En caso de no poder convertir, se mantienen los datos originales

        return dataframe

    def get_stored_table(self, category, firebase=False, title=None, column=None, just_column=False, column_value=None):
        if firebase:
            tables = self.get_data_by_path(category)
        else:
            tables = {k: v for k, v in self.data_tables.items() if k[0] == category}
        if title:
            if column:
                df = tables.get((category, title))
                if column_value:
                    print(df)
                    df = pd.DataFrame(df)
                    df = df.loc[df[column] == column_value]
                    if just_column:
                        return df[column]
                    else:
                        return df
                else:
                    if just_column:
                        return df[column]
            else:
                return tables.get(category, title)
        else:
            return tables
