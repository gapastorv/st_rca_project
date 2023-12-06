import tabula
import pandas as pd
from PIL import Image
import fitz
import re

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
                                     lattice= True if lat else False, relative_columns=True)
        return table_data, title

    def clean_unnamed_columns(self, title):
        component, title = self.extract_tables(title, 1)
        refined_data = []
        for data in component:
            data = data.loc[:, ~data.columns.str.contains('^Unnamed')]
            refined_data.append(data)
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

        compiled[title] = value
        return compiled

