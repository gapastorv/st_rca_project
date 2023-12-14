import streamlit as st


class Extras:
    @staticmethod
    def remove_sidebar():
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"]{
                visibility: hidden;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

    @staticmethod
    def remove_canvas_table():
        st.markdown(
            """
            <style> 
            [data-testid="stDocstring"]{
                visibility: hidden;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

    @staticmethod
    def change_metric_style(size):
        st.markdown(
            f"""
        <style>
        [data-testid="stMetricValue"] {{
            font-size: {size}px;
        }}
        </style>
        """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def get_attributes_names(atribute_type):
        json_data = {'Tear Down': ['Bomba', 'Intake', 'Protector', 'Motor', 'Sensor', 'Cable'],
                     'DIFA': ['Resumen-tr', 'Equipo', 'Antecedentes', 'Eventos', 'Producción'],
                     'Pull': ['Cable de descarga', 'Bomba', 'Intake', 'Protector', 'Motor', 'Sensor', 'Cable de motor',
                              'Observaciones'],
                     'Matching': ['General-tr', 'Condición de bombeo-tr', 'Bomba-tr', 'Motor-tr']}

        main_fields = {'Tear Down': ['Cliente', 'Pozo', 'Runlife', 'Fecha instalación', 'Fecha parada', 'Fecha pull',
                                     'Razón pull'],
                       'Pull': ['Pozo', 'Campo', 'País', 'Fecha instalación', 'Fecha parada', 'Fecha pull', 'Runlife',
                                'Razón pull'],
                       'DIFA': ['Cliente', 'Pozo', 'Runlife', 'Fecha instalación', 'Fecha parada', 'Fecha pull',
                                'Razón pull'],
                       'Matching': ['Pozo', 'Manufactura', 'Runlife', 'Bomba', 'Motor', 'Fecha instalación',
                                    'Fecha simulacion']
                       }

        if atribute_type == 'text':
            return main_fields
        else:
            return json_data
