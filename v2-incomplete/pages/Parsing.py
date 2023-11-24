import pandas as pd
import streamlit as st
import fitz
from PIL import Image
from dataExtractor import DataExtractor
from image2 import Canvas
from firebase import FirebaseDB
import json
from st_keyup import st_keyup

json_data = {'Tear Down': ['cable', 'bomba', 'intake'],
             'Production': ['simulacion', 'equipo'],
             'Artificial Lift': ['cable', 'bomba', 'intake', 'motor', 'sensor', 'protector'],
             'Efficiency': ['general', 'bomba', 'motor']}

st.write(f"Define a new extraction {st.session_state.user['nombre']}")

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


def get_report_main_topics(report):
    st.session_state.atributos_reporte = json_data[report]


def add_coordinates_to_firebase(dataframe, collection_name, subject):
    firebase_db = FirebaseDB()
    return firebase_db.add_coordinates(dataframe, collection_name, subject)


def selection():
    # Usage example
    subject_name = "testmail/test2"
    #To upload a report
    st.subheader("PDF Document Extraction")
    uploaded_file = st.file_uploader("Upload PDF sample", type=['pdf'])
    realtime_update = st.checkbox("Update in realtime", True)
    st.write("Select between defining the area of the table (rect),"
             "or modify a predefined area (transform)")
    drawing_mode = st.selectbox("Drawing tool:", ["rect", "transform"])

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

        st.caption("Note: This canvas version could define columns or cells with None values,"
                   " consider to select a table or area of it in order that the table extraction preview"
                   " contains the elements you want.")

        present_dataframe(st.session_state["compiled_scales"], "All Scaled Coordinates")

        objects_df = canvas_obj.get_objects_dataframe()
        all_scaled_coordinates = None
        if objects_df is not None and 'type' in objects_df.columns:
            table_objects = objects_df.loc[objects_df['type'] == 'rect']

            if len(table_objects) > 0:
                difference = (len(st.session_state["atributos_reporte"])-len(st.session_state["compiled_scales"]))
                #st.write(difference)
                data = st.session_state["atributos_reporte"][-difference:] if difference > 0 else []
                #st.write(data)
                all_scaled_coordinates = canvas_obj.process_tables(table_objects,
                                                                   pdf.load_page(st.session_state["page_number"]),
                                                                   data)
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
                        titles = row['Title']

                        data_extractor = DataExtractor(uploaded_file, st.session_state["page_number"] + 1, top, left,
                                                       width, height)
                        tables, title = data_extractor.extract_tables(titles)

                        if tables:
                            st.subheader(f"Table {titles}")
                            table_count += 1
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
                st.session_state["compiled_scales"] = pd.concat([st.session_state["compiled_scales"],
                                                                 new_scaled_coordinates], ignore_index=True)
            if st.session_state["page_number"] >= len(image_list) - 1:
                # st.session_state["page_number"] = 0
                st.session_state["disabled"] = True

            canvas_obj.reset_canvas(image_list[st.session_state["page_number"]], st.session_state["page_number"])

        if st.session_state["disabled"]:
            st.write("Before you save, define the mail subject for extraction (this implies how will be the subject"
                     " text when an email arrives to your inbox):")
            subject_value = st_keyup("", value="Report_sample", key="subject")
            st.write(f"Subject: {subject_value}")
            subject = st.session_state.user['email'] + "/" + subject_value
            subject_name = subject.replace(" ", "_")
            st.write(f"Final parameters: {subject}")

        if save_button:
            st.session_state["page_number"] += 1
            new_scaled_coordinates = store_scaled_coordinates(st.session_state["page_number"], all_scaled_coordinates,
                                                              ["scaleX", "scaleY", "Width", "Height"])
            if new_scaled_coordinates is not None:
                st.session_state["compiled_scales"] = pd.concat([st.session_state["compiled_scales"],
                                                                 new_scaled_coordinates], ignore_index=True)
            present_dataframe(st.session_state["compiled_scales"], "Final Scaled Coordinates")

            id_num = add_coordinates_to_firebase(st.session_state["compiled_scales"], "db_coord", subject_name)
            st.markdown("Data saved with id " + str(id_num))
            st.button("Finish", on_click= lambda : reset_all(uploaded_file))

        canvas_obj.display_canvas()
    else:
        st.session_state["page_number"] = 0
        st.session_state["disabled"] = False
        st.session_state["compiled_scales"] = pd.DataFrame()


# Función para mostrar la pantalla dependiendo del botón seleccionado
def mostrar_pantalla():
    # Inicializar el session state
    if 'boton_seleccionado' not in st.session_state:
        st.session_state.boton_seleccionado = None

    if 'input_text' not in st.session_state:
        st.session_state.input_text = False

    if not st.session_state.user['imap']:
        st.header("Additional process")
        st.subheader("As this app works with email (IMAP), it is important to get access to your email account.")
        input_text = st.text_input("Input you mail password", key='input_text_value')
        if st.button("Save"):
            firebasedb = FirebaseDB()
            firebasedb.set_user_data(st.session_state.user['uid'], 'ek', input_text)
            # Cambia el valor a True para mostrar los botones
            st.session_state.user['imap'] = True
        st.caption(":red[Gmail:] _For Gmail accounts, it is important to enable IMAP and input an app password, "
                   "for this you can look at the next link:_ https://support.google.com/mail/answer/185833?hl=es-419")
    else:
        # Mostrar el header dependiendo del botón seleccionado
        if st.session_state.boton_seleccionado is not None:
            if 'atributos_reporte' not in st.session_state:
                st.session_state.atributos_reporte = []

            st.header(f"Report type: {st.session_state.boton_seleccionado}")
            print(st.session_state.boton_seleccionado)
            get_report_main_topics(st.session_state.boton_seleccionado)
            print(st.session_state.atributos_reporte)
            st.write(st.session_state.atributos_reporte)
            selection()

        # Botones para seleccionar
        if st.session_state.boton_seleccionado is None:
            if st.button('Tear Down', key='button1',
                         on_click=lambda: st.session_state.update(boton_seleccionado="Tear Down")):
                pass
            if st.button('Production', key='button2',
                         on_click=lambda: st.session_state.update(boton_seleccionado="Production")):
                pass
            if st.button('Artificial Lift', key='button3',
                         on_click=lambda: st.session_state.update(boton_seleccionado="Artificial Lift")):
                pass
            if st.button('Efficiency', key='button4',
                         on_click=lambda: st.session_state.update(boton_seleccionado="Efficiency")):
                pass

        if st.session_state.boton_seleccionado is None:
            st.write("Please, select a report type")


# Mostrar la pantalla
mostrar_pantalla()

def reset_all(file):
    st.session_state.boton_seleccionado = None
    st.session_state["page_number"] = 0
    st.session_state["disabled"] = False
    st.session_state["compiled_scales"] = pd.DataFrame()
    file = None