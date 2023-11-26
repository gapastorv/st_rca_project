import tabula
import pandas as pd
from firebase import FirebaseDB


class DataExtractor:
    def __init__(self, file, page_number, top, left, width, height):
        self.file = file
        self.page_number = page_number
        self.top = top
        self.left = left
        self.width = width
        self.height = height

    def extract_tables(self, title):
        area = (self.top, self.left, self.top + self.height, self.left + self.width)
        table_data = tabula.read_pdf(self.file, pages=self.page_number, area=area,
                                     relative_columns=True)
        return table_data, title



