import pandas as pd
import streamlit as st
import fitz
from PIL import Image
from dataExtractor import DataExtractor
from image2 import Canvas
from firebase import FirebaseDB


def read_pdf(uploaded):
    file = fitz.open(stream=uploaded.read())
    return file


def create_image_list_from_pdf(file):
    images = []
    for page_number in range(len(file)):
        page = file.load_page(page_number)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        w, h = 700, 500
        resized_image = image.resize((w, h))
        images.append(resized_image)
    return images


def replace_image_in_canvas(canvas, image, key):
    new_image = image  # Get the new image
    new_key = key  # Get the new key
    canvas.reset_canvas(new_image, new_key)  # Call the reset_canvas method of the canvas object


def load_canvas(image, page_number, draw_mode, update):
    canvas = Canvas(image, draw_mode, update_streamlit=update)
    canvas.create_canvas(page_number)
    canvas.process_drawing()
    return canvas


def store_scaled_coordinates(page_number, coordinates, delete_columns):
    if coordinates is not None:
        # Fill the 'page' column with the page_number value
        coordinates['page'] = page_number

        # Drop the specified columns
        coordinates = coordinates.drop(delete_columns, axis=1)

        return pd.DataFrame(coordinates)


def present_dataframe(dataframe, markdown):
    if isinstance(dataframe, pd.DataFrame):
        st.subheader(markdown)
        st.dataframe(dataframe)
    else:
        st.write("No DataFrame was provided.")


def first_page():
    st.subheader("PDF Document")
    st.write("Upload and define attributes.")
    file = st.file_uploader("Upload PDF", type=['pdf'])
    if file is not None:
        if "file" not in st.session_state:
            st.session_state["file"] = file

        if "regex" not in st.session_state:
            st.session_state["regex"] = pd.DataFrame()

        if "subject" not in st.session_state:
            st.session_state["subject"] = None


def add_coordinates_to_firebase(dataframe, collection_name, subject):
    firebase_db = FirebaseDB()
    return firebase_db.add_coordinates(dataframe, collection_name, subject)


# Usage example
subject_name = "testmail/test"
uploaded_file = st.sidebar.file_uploader("Upload PDF", type=['pdf'])
realtime_update = st.sidebar.checkbox("Update in realtime", True)
drawing_mode = st.sidebar.selectbox("Drawing tool:", ["rect", "transform"])

if uploaded_file is not None:
    if "compiled_scales" not in st.session_state:
        st.session_state["compiled_scales"] = pd.DataFrame()

    if "page_number" not in st.session_state:
        st.session_state["page_number"] = 0

    pdf = read_pdf(uploaded_file)
    image_list = create_image_list_from_pdf(pdf)

    canvas_obj = load_canvas(image_list[st.session_state["page_number"]],
                             st.session_state["page_number"],
                             drawing_mode, realtime_update)

    present_dataframe(st.session_state["compiled_scales"], "All Scaled Coordinates")

    objects_df = canvas_obj.get_objects_dataframe()
    all_scaled_coordinates = None
    if objects_df is not None and 'type' in objects_df.columns:
        table_objects = objects_df.loc[objects_df['type'] == 'rect']

        if len(table_objects) > 0:
            all_scaled_coordinates = canvas_obj.process_tables(table_objects,
                                                               pdf.load_page(st.session_state["page_number"]))
            if all_scaled_coordinates is not None:
                st.markdown("### Scaled Page Coordinates")
                st.table(all_scaled_coordinates)

                st.markdown("### Extracted Page Tables")

                table_count = 0

                for _, row in all_scaled_coordinates.iterrows():
                    top = row['Top']
                    left = row['Left']
                    height = row['Final height']
                    width = row['Final width']

                    data_extractor = DataExtractor(uploaded_file, st.session_state["page_number"] + 1, top, left,
                                                   width, height)
                    tables = data_extractor.extract_tables()

                    if tables:
                        table_count += 1
                        st.subheader(f"Table {table_count}")
                        for i in range(len(tables)):
                            st.dataframe(tables[i])
                    else:
                        st.write("No tables were extracted.")

            else:
                st.write("No rectangle selections found on the canvas.")

    else:
        st.write("No rectangle selections found on the canvas.")

    canvas_element = st.empty()  # Create an empty element to display the canvas

    if "disabled" not in st.session_state:
        st.session_state["disabled"] = False

    next_button = st.button("Next", disabled=st.session_state["disabled"])
    save_button = st.button("Save", disabled=not st.session_state["disabled"])

    if next_button:
        canvas_element.empty()  # Clear the canvas element
        st.session_state["page_number"] += 1
        new_scaled_coordinates = store_scaled_coordinates(st.session_state["page_number"], all_scaled_coordinates,
                                                          ["scaleX", "scaleY", "Width", "Height"])
        if new_scaled_coordinates is not None:
            st.session_state["compiled_scales"] = st.session_state["compiled_scales"].append(new_scaled_coordinates,
                                                                                             ignore_index=True)
        if st.session_state["page_number"] >= len(image_list) - 1:
            # st.session_state["page_number"] = 0
            st.session_state["disabled"] = True

        canvas_obj.reset_canvas(image_list[st.session_state["page_number"]], st.session_state["page_number"])

    if save_button:
        st.session_state["page_number"] += 1
        new_scaled_coordinates = store_scaled_coordinates(st.session_state["page_number"], all_scaled_coordinates,
                                                          ["scaleX", "scaleY", "Width", "Height"])
        if new_scaled_coordinates is not None:
            st.session_state["compiled_scales"] = st.session_state["compiled_scales"].append(new_scaled_coordinates,
                                                                                             ignore_index=True)
        present_dataframe(st.session_state["compiled_scales"], "All Scaled Coordinates")

        id_num = add_coordinates_to_firebase(st.session_state["compiled_scales"], "db_coord", subject_name)
        st.markdown("Data saved with id " + str(id_num))

    canvas_obj.display_canvas()
else:
    st.session_state["page_number"] = 0
    st.session_state["compiled_scales"] = pd.DataFrame()
