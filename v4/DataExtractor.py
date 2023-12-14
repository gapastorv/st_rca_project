import tabula
import pandas as pd
from PIL import Image
import fitz
import re
import numpy as np


class DataExtractor:
    def __init__(self, file, page_number, top, left, width, height):
        self.file = file
        self.page_number = page_number
        self.top = top
        self.left = left
        self.width = width
        self.height = height

    def extract_tables(self, title, lat):
        area = (self.top, self.left, self.top + self.height, self.left + self.width)
        table_data = tabula.read_pdf(self.file, pages=self.page_number, area=area,
                                     lattice=True if lat else False, relative_columns=True,
                                     force_subprocess=True)
        return table_data, title

    @staticmethod
    def clean_data(data, transpose):
        if transpose:
            data = data.dropna(axis=0, how='all')
            print(data)
            new_df = pd.DataFrame()
            column_head = data.columns[0]
            column_data = data.columns[1:]
            for index, row in data.iterrows():
                column_name = row[0]  # Primer elemento de la fila como nombre de columna
                new_df[column_name] = row[1:]  # Agregar la fila (excluyendo el primer elemento) como columna

            new_df.insert(0, f'{column_head}', column_data)
            new_df.index = range(len(new_df))

            data = new_df.astype(str)

            # Filtrar las columnas que contienen 'Unnamed' en su nombre
            unnamed_columns = [col for col in data.columns if
                               not (isinstance(col, float) and np.isnan(col)) and 'Unnamed' not in str(col)]
            data = data[unnamed_columns].dropna()
        else:
            data = data.loc[:, ~data.columns.str.contains('^Unnamed')].dropna()
        return data

    def re_get_data(self, title, lattice, index):
        component, title = self.extract_tables(title, lattice)
        return component[index]

    def clean_unnamed_columns(self, title):
        lattice = 1
        component, title = self.extract_tables(title, lattice)
        if len(component) == 0:
            lattice = 0
            component, title = self.extract_tables(title, lattice)

        refined_data = []
        for index, data in enumerate(component):
            data_transformed = self.clean_data(data, True if '-tr' in title else False)
            if data_transformed.empty:
                lattice = 1 if lattice == 0 else 0
                data_transformed = self.re_get_data(title, lattice, index)
                data_transformed = self.clean_data(data_transformed, True if '-tr' in title else False)
            print(data_transformed)
            refined_data.append(data_transformed)
        return refined_data, title

    def create_image(self):
        page = self.file.load_page(self.page_number)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        w, h = 700, 700
        resized_image = image.resize((w, h))
        return resized_image

    def get_text(self, title, condition):
        component, title = self.extract_tables(title, 0)
        if len(component) == 0:
            component, title = self.extract_tables(title, 1)
        print(len(component))
        print(component[0])
        start_0 = re.findall('^Empty DataFrame', str(component[0]))
        start_1 = re.findall('^Empty DataFrame', str(component[0]))
        if start_0:
            # Define the pattern to match the string between 'Columns: [' and ']'
            pattern = r'Columns: \[([^\]]+)\]'
            result_string = re.search(pattern, str(component[0])).group(1)
            return result_string
        else:
            df = pd.DataFrame(component[0])
            # Convertir DataFrame a diccionario con el formato deseado
            dict_result = df.to_dict(orient='records')[0]
            print(dict_result)
            return list(dict_result.keys())[0] if condition else list(dict_result.values())[0]

    @staticmethod
    def compile_fields(table, title, value):
        compiled = {}
        if bool(table):
            compiled = table

        compiled[title] = f"{compiled[title]}, {value}" if title in compiled else value
        return compiled

# save_data("uploaded_pdf.pdf", "testmail", "test")
