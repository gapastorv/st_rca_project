from streamlit_drawable_canvas import st_canvas
import streamlit as st
import pandas as pd


class Canvas:
    def __init__(self, image, drawing_mode, update_streamlit=True):
        self.image = image
        self.drawing_mode = drawing_mode
        self.update_streamlit = update_streamlit
        self.canvas = None
        self.json_data = None
        self.scaled_coordinates = None
        self.key = None

    def create_canvas(self, key):
        self.key = key
        self.canvas = st_canvas(
            drawing_mode=self.drawing_mode,
            height=self.image.height,
            width=self.image.width,
            stroke_width=1,
            fill_color="rgba(255, 0, 0, 0.15)",
            background_image=self.image,
            update_streamlit=self.update_streamlit,
            key=self.key
        )

    def update_canvas(self, new_image, new_key):
        self.image = new_image
        self.key = new_key
        self.canvas = st_canvas(
            drawing_mode=self.drawing_mode,
            height=self.image.height,
            width=self.image.width,
            stroke_width=1,
            fill_color="rgba(255, 0, 0, 0.15)",
            background_image=self.image,
            update_streamlit=self.update_streamlit,
            key=self.key
        )

    def process_drawing(self):
        if self.canvas.json_data is not None:
            self.json_data = self.canvas.json_data

    def get_objects_dataframe(self):
        if self.json_data:
            objects = pd.json_normalize(self.json_data["objects"])
            for col in objects.select_dtypes(include=['object']).columns:
                objects[col] = objects[col].astype("str")
            return objects
        return None

    def process_tables(self, table_objects, page, table_titles):
        if len(table_objects) > 0:
            all_scaled_coordinates = pd.DataFrame(columns=["Left", "Top", "Width", "Height", "scaleX", "scaleY"])
            table_count = 0
            for _, row in table_objects.iterrows():

                table_left = row['left']
                table_top = row['top']
                table_width = row['width']
                table_height = row['height']
                scale_x = row["scaleX"]
                scale_y = row["scaleY"]

                # Scale the coordinates based on the page size
                page_width = page.rect.width
                page_height = page.rect.height

                table_left_scaled = table_left * page_width / self.image.width
                table_top_scaled = table_top * page_height / self.image.height
                table_width_scaled = table_width * page_width / self.image.width
                table_height_scaled = table_height * page_height / self.image.height
                table_final_width = scale_x * table_width_scaled
                table_final_height = scale_y + table_height_scaled
                try:
                    title = table_titles[table_count]  # Intenta obtener el título si está disponible en table_titles
                except IndexError:
                    title = f'Extra table {table_count}'  # Si no hay suficientes títulos, establece un título genérico
                scaled_coordinates = pd.DataFrame({
                    "Top": [table_top_scaled],
                    "Left": [table_left_scaled],
                    "Width": [table_width_scaled],
                    "Height": [table_height_scaled],
                    "scaleX": [scale_x],
                    "scaleY": [scale_y],
                    "Final height": [table_final_height],
                    "Final width": [table_final_width],
                    "Title": [title]
                })
                table_count += 1
                all_scaled_coordinates = pd.concat([all_scaled_coordinates, scaled_coordinates])
                self.scaled_coordinates = all_scaled_coordinates

            return all_scaled_coordinates

        return None

    def display_canvas(self):
        if self.canvas:
            st.write(self.canvas)

    def reset_canvas(self, new_image, key):
        self.image = new_image
        self.key = key
        self.canvas = st_canvas(
            drawing_mode=self.drawing_mode,
            height=self.image.height,
            width=self.image.width,
            stroke_width=1,
            fill_color="rgba(255, 0, 0, 0.15)",
            background_image=self.image,
            update_streamlit=self.update_streamlit,
            key=self.key
        )
        self.json_data = None
