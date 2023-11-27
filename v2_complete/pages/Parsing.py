import streamlit as st
from firebase import FirebaseDB
import json
from st_keyup import st_keyup
import base64
import pandas as pd
import fitz
from dataExtractor import DataExtractor
from image2 import Canvas
import subprocess

json_data = {'Tear Down': ['cable', 'bomba', 'intake'],
             'Production': ['simulacion', 'equipo'],
             'Artificial Lift': ['cable', 'bomba', 'intake', 'motor', 'sensor', 'protector'],
             'Efficiency': ['general', 'bomba', 'motor']}

main_fields = ['Pozo', 'Campo', 'País', 'Fecha_instalación', 'Fecha_pull', 'Runlife', 'Razón_pull']


# if 'user' not in st.session_state:
#     st.session_state.user = {
#         'uid': 's66s46sf46d',
#         'name': 'longo',
#         'imap': True,
#         'email': 'loco@gmail.com'
#     }


def get_report_main_topics(report):
    if report != 's':
        st.session_state.atributos_reporte = json_data[report]
    else:
        st.session_state.atributos_reporte = main_fields


def start_parsing(subject_value):
    st.session_state.subject = subject_value
    st.session_state.update(parsing=1)


def subject_submit():
    st.write("Before you continue, define the mail subject for extraction (this implies how will be the subject"
             " text when an email arrives to your inbox):")
    subject_value = st_keyup("", value="Report_sample", key="subject")
    st.write(f"Subject: {subject_value}")
    subject = st.session_state.user['email'] + "/" + subject_value
    subject_name = subject.replace(" ", "_")
    st.write(f"Final parameters: {subject_name}")
    if st.button('Start Parsing', key='subject_btn', on_click=lambda: start_parsing(subject_name)):
        pass


def imap_confirm(input_text):
    firebase = FirebaseDB()
    firebase.set_user_data(st.session_state.user['uid'], 'mailk', input_text)
    # Cambia el valor a True para mostrar los botones
    st.session_state.user['imap'] = True


def imap_cred():
    st.header("Additional process")
    st.subheader("As this app works with email (IMAP), it is important to get access to your email account.")
    input_text = st.text_input("Input you mail password", key='input_text_value')
    if st.button("Save", key='imap_save', on_click=lambda: imap_confirm(input_text)):
        pass

    st.caption(":red[Gmail:] _For Gmail accounts, it is important to enable IMAP and input an app password, "
               "for this you can look at the next link:_ https://support.google.com/mail/answer/185833?hl=es-419")


def file_data(upload_file):
    # Procesar el archivo cargado, por ejemplo, leer su contenido
    file_content = upload_file.read()

    # Codificar el contenido binario en base64
    file_content_base64 = base64.b64encode(file_content).decode('utf-8')

    # Generar un diccionario con la información del archivo, incluyendo el contenido binario codificado
    file_info = {
        "filename": upload_file.name,
        "content_type": upload_file.type,
        "size": len(file_content),
        "content_base64": file_content_base64
    }

    # Convertir el diccionario a formato JSON
    file_json = json.dumps(file_info, indent=4)
    return file_json


def restart_all():
    st.session_state.boton_seleccionado = None
    st.session_state.subject = None
    st.session_state.parsing = 0
    st.session_state.file = None
    st.session_state.atributos_reporte = []


def read_pdf(uploaded):
    file = fitz.open(stream=uploaded.read())
    return file


def create_image_list_from_pdf(file):
    images = []
    for page_number in range(len(file)):
        data = DataExtractor(file, page_number, 0, 0, 0, 0)
        images.append(data.create_image())
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


def add_coordinates_to_firebase(dataframe, collection_name, subject, type):
    firebase_db = FirebaseDB()
    return firebase_db.add_coordinates(dataframe, collection_name, subject, type)


def parsing():
    if 'file' not in st.session_state:
        st.session_state.file = None

    if 'temp_subject' not in st.session_state:
        st.session_state.temp_subject = st.session_state.subject

    if 'pdf' not in st.session_state:
        st.session_state.pdf = None

    st.header(f"Parsing: {st.session_state.boton_seleccionado}")
    upload_file = st.file_uploader("Upload PDF sample", type=['pdf'])
    st.write(st.session_state.temp_subject)
    # st.write(st.session_state.user)
    st.write(st.session_state.atributos_reporte)
    realtime_update = st.checkbox("Update in realtime", True)
    st.write("Select between defining the area of the table (rect),"
             "or modify a predefined area (transform)")
    drawing_mode = st.selectbox("Drawing tool:", ["rect", "transform"])
    if upload_file is not None:
        st.session_state.file = upload_file
        # Mostrar el JSON resultante en la interfaz
        # st.text("JSON representation of the uploaded file:")
        # st.code(file_data(st.session_state.file), language='json')

        if "text_compiled_scales" not in st.session_state:
            st.session_state["text_compiled_scales"] = pd.DataFrame()

        if "page_number" not in st.session_state:
            st.session_state["page_number"] = 0

        pdf = read_pdf(st.session_state.file)
        st.session_state.pdf = pdf
        image_list = create_image_list_from_pdf(pdf)

        canvas_obj = load_canvas(image_list[st.session_state["page_number"]],
                                 st.session_state["page_number"],
                                 drawing_mode, realtime_update)

        st.caption("Note: This canvas version implies the use of OCR, but applying tabula, and regex for"
                   " parsing, consider to not select here a wide area, just try to select the place of the "
                   "text field you want to extract, although it could occur that some text fields could require "
                   "a different selection. Based on that, be careful with the text you want to obtain.")

        present_dataframe(st.session_state["text_compiled_scales"], "All Scaled Coordinates")

        objects_df = canvas_obj.get_objects_dataframe()
        all_scaled_coordinates = None
        if objects_df is not None and 'type' in objects_df.columns:
            table_objects = objects_df.loc[objects_df['type'] == 'rect']

            if len(table_objects) > 0:
                difference = (
                        len(st.session_state.atributos_reporte) - len(st.session_state["text_compiled_scales"]))
                # st.write(difference)
                data = st.session_state.atributos_reporte[-difference:] if difference > 0 else []
                # st.write(data)
                all_scaled_coordinates = canvas_obj.process_tables(table_objects,
                                                                   pdf.load_page(st.session_state["page_number"]),
                                                                   data)

                if all_scaled_coordinates is not None:
                    st.markdown("### Scaled Page Coordinates")
                    st.table(all_scaled_coordinates)

                    st.markdown("### Extracted Page Text")

                    table_count = 0

                    general_table = {}

                    for _, row in all_scaled_coordinates.iterrows():
                        top = row['Top']
                        left = row['Left']
                        height = row['Final height']
                        width = row['Final width']
                        titles = row['Title']

                        try:
                            data_extractor = DataExtractor(st.session_state.file, st.session_state["page_number"] + 1,
                                                           top,
                                                           left, width, height)
                            string = data_extractor.get_text(titles, 0)

                            if string:
                                st.subheader(f"Text {titles}")
                                table_count += 1
                                st.write(string)
                                general_table[titles] = string
                            else:
                                st.write("No text was extracted.")
                        except IndexError as e:
                            st.error(f"An IndexError occurred for the {titles} text, \n"
                                     f"consider to select a wide area, although this could\n "
                                     f"happen because of not black color characters or the\n "
                                     f"area does not contain any text.")
                        except subprocess.CalledProcessError as e:
                            st.error(f"An error occurred during the extraction of the {titles} field, \n"
                                     f"In these cases, select the row or field above the one you want to extract, \n"
                                     f"this could help to extract the main field for now.")
                        except Exception as e:
                            st.error(
                                f"An unexpected error occurred during data extraction, try it better "
                                f"in another region or later.")

                    st.markdown("### Current Extracted Page Fields")
                    print(general_table)
                    st.dataframe(general_table)
                else:
                    st.write("No selections found on the canvas.")

        else:
            st.write("No rectangle selections found on the canvas.")

        canvas_element = st.empty()  # Create an empty element to display the canvas

        if "disabled" not in st.session_state:
            st.session_state["disabled"] = False

        next_button = st.button("Next", disabled=st.session_state["disabled"])
        save_button = st.button("Save", disabled=not st.session_state["disabled"])

        if next_button:
            print(st.session_state.subject)
            print(st.session_state.user)
            canvas_element.empty()  # Clear the canvas element
            st.session_state["page_number"] += 1
            new_scaled_coordinates = store_scaled_coordinates(st.session_state["page_number"], all_scaled_coordinates,
                                                              ["scaleX", "scaleY", "Width", "Height"])
            if new_scaled_coordinates is not None:
                st.session_state["text_compiled_scales"] = pd.concat([st.session_state["text_compiled_scales"],
                                                                      new_scaled_coordinates], ignore_index=True)
            if st.session_state["page_number"] >= len(image_list) - 1:
                # st.session_state["page_number"] = 0
                st.session_state["disabled"] = True

            canvas_obj.reset_canvas(image_list[st.session_state["page_number"]], st.session_state["page_number"])

        if save_button:
            st.session_state["page_number"] += 1
            new_scaled_coordinates = store_scaled_coordinates(st.session_state["page_number"], all_scaled_coordinates,
                                                              ["scaleX", "scaleY", "Width", "Height"])
            if new_scaled_coordinates is not None:
                st.session_state["text_compiled_scales"] = pd.concat([st.session_state["text_compiled_scales"],
                                                                      new_scaled_coordinates], ignore_index=True)
            if not st.session_state["text_compiled_scales"].empty:
                present_dataframe(st.session_state["text_compiled_scales"], "Final Scaled Coordinates")

                id_num = add_coordinates_to_firebase(st.session_state["text_compiled_scales"], "db_coord",
                                                     st.session_state.temp_subject, 'text')
                st.markdown("Data saved with id " + str(id_num))
            else:
                st.markdown("No data saved")
            st.button('Move to tables', key='parsed', on_click=lambda: st.session_state.update(parsing=2))

        canvas_obj.display_canvas()

    else:
        st.session_state.file = None
        st.session_state["page_number"] = 0
        st.session_state["disabled"] = False
        st.session_state["text_compiled_scales"] = pd.DataFrame()

    # st.button('Cancel', key='cancel', on_click=lambda: restart_all())


def selection():
    if 'final_subject' not in st.session_state:
        st.session_state.final_subject = st.session_state.temp_subject

    if 'final_file' not in st.session_state:
        st.session_state.final_file = st.session_state.file

    if 'final_page' not in st.session_state:
        st.session_state.final_page = 0

    st.header(f"Tables: {st.session_state.boton_seleccionado}")
    st.write(st.session_state.final_subject)
    realtime_update = st.checkbox("Update in realtime", True)
    st.write("Select between defining the area of the table (rect),"
             "or modify a predefined area (transform)")
    drawing_mode = st.selectbox("Drawing tool:", ["rect", "transform"])
    st.write(st.session_state.atributos_reporte)
    #st.session_state["page_number"] = 0
    #st.session_state["disabled"] = False
    st.session_state["text_compiled_scales"] = pd.DataFrame()

    if "compiled_scales" not in st.session_state:
        st.session_state["compiled_scales"] = pd.DataFrame()

    # Mostrar el JSON resultante en la interfaz
    # st.text("JSON representation of the uploaded file:")
    # st.code(file_data(st.session_state.file), language='json')
    image_list = create_image_list_from_pdf(st.session_state.pdf)

    canvas_obj = load_canvas(image_list[st.session_state.final_page],
                             st.session_state.final_page,
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
            difference = (len(st.session_state["atributos_reporte"]) - len(st.session_state["compiled_scales"]))
            # st.write(difference)
            data = st.session_state["atributos_reporte"][-difference:] if difference > 0 else []
            # st.write(data)
            all_scaled_coordinates = canvas_obj.process_tables(table_objects,
                                                               st.session_state.pdf.load_page(
                                                                   st.session_state.final_page),
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

                    try:

                        data_extractor = DataExtractor(st.session_state.file,
                                                       st.session_state.final_page + 1,
                                                       top,
                                                       left, width, height)
                        tables, title = data_extractor.extract_tables(titles)

                        if tables:
                            st.subheader(f"Table {titles}")
                            table_count += 1
                            for i in range(len(tables)):
                                st.dataframe(tables[i])
                        else:
                            st.write("No table was extracted.")
                    except IndexError as e:
                        st.error(f"An IndexError occurred for the {titles} table, \n"
                                 f"consider to select a wide area, although this could\n "
                                 f"happen because of not black color characters or the\n "
                                 f"area does not contain any table.")
                    except Exception as e:
                        st.error(
                            f"An unexpected error occurred during data extraction, try it better "
                            f"in another region or later.")


            else:
                st.write("No selections found on the canvas.")

    else:
        st.write("No rectangle selections found on the canvas.")

    canvas_element = st.empty()  # Create an empty element to display the canvas

    if "disabled_select" not in st.session_state:
        st.session_state["disabled_select"] = False

    next_button = st.button("Next", disabled=st.session_state["disabled_select"])
    save_button = st.button("Save", disabled=not st.session_state["disabled_select"])

    if next_button:
        print(st.session_state.final_page)
        canvas_element.empty()  # Clear the canvas element
        st.session_state.final_page += 1
        new_scaled_coordinates = store_scaled_coordinates(st.session_state.final_page, all_scaled_coordinates,
                                                          ["scaleX", "scaleY", "Width", "Height"])
        if new_scaled_coordinates is not None:
            st.session_state["compiled_scales"] = pd.concat([st.session_state["compiled_scales"],
                                                             new_scaled_coordinates], ignore_index=True)
        if st.session_state.final_page >= len(image_list) - 1:
            # st.session_state.final_page = 0
            st.session_state["disabled_select"] = True

        canvas_obj.reset_canvas(image_list[st.session_state.final_page], st.session_state.final_page)

    if save_button:
        st.session_state.final_page += 1
        new_scaled_coordinates = store_scaled_coordinates(st.session_state.final_page, all_scaled_coordinates,
                                                          ["scaleX", "scaleY", "Width", "Height"])
        if new_scaled_coordinates is not None:
            st.session_state["compiled_scales"] = pd.concat([st.session_state["compiled_scales"],
                                                             new_scaled_coordinates], ignore_index=True)

        if not st.session_state["compiled_scales"].empty:
            present_dataframe(st.session_state["compiled_scales"], "Final Scaled Coordinates")

            id_num = add_coordinates_to_firebase(st.session_state["compiled_scales"], "db_coord",
                                                 st.session_state.final_subject, 'tables')
            firebase = FirebaseDB()
            firebase.set_user_data(st.session_state.user['uid'], 'subjects', st.session_state.final_subject.split('/')[1])
            firebase.set_user_data(st.session_state.user['uid'], 'access', True)
            st.markdown("Data saved with id " + str(id_num))
        else:
            st.markdown("No data saved")
        st.button("Finish", on_click=lambda: restart_all())

    canvas_obj.display_canvas()

    # st.button('Cancel', key='cancel', on_click=lambda: restart_all())


def mostrar_pantalla():
    # Inicializar el session state
    if 'boton_seleccionado' not in st.session_state:
        st.session_state.boton_seleccionado = None

    if 'subject' not in st.session_state:
        st.session_state.subject = None

    if 'parsing' not in st.session_state:
        st.session_state.parsing = 0

    if not st.session_state.user['imap']:
        imap_cred()
    else:
        # Mostrar el header dependiendo del botón seleccionado
        if st.session_state.boton_seleccionado is not None:
            if 'atributos_reporte' not in st.session_state:
                st.session_state.atributos_reporte = []

            st.header(f"Report type: {st.session_state.boton_seleccionado}")
            print(st.session_state.boton_seleccionado)
            get_report_main_topics(st.session_state.boton_seleccionado)
            print(st.session_state.atributos_reporte)

            if st.session_state.parsing == 0:
                subject_submit()
            if st.session_state.parsing == 1:
                get_report_main_topics('s')
                print(st.session_state.atributos_reporte)
                print(st.session_state.subject)
                parsing()
            if st.session_state.parsing == 2:
                get_report_main_topics(st.session_state.boton_seleccionado)
                print(st.session_state.atributos_reporte)
                print(st.session_state.subject)
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


mostrar_pantalla()
