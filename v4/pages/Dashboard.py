import streamlit as st
from DataManager import DataManager
from Extras import Extras
import plotly.express as px
import pandas as pd
import warnings

warnings.filterwarnings("ignore")


def get_well_names(data_manager):
    categories_list = data_manager.get_categories()
    wells = []
    for category in categories_list:
        well_values = data_manager.get_stored_table(category, True, 'general', 'Pozo', True)
        wells += well_values
    wells = set(wells)
    return wells


def plot_series(x, y, dataframe):
    if len(dataframe[x]) != len(dataframe[y]):
        st.error("The series can not be plotted, the dimensions do not fit.")
        return

    df = pd.DataFrame({x: dataframe[x], y: dataframe[y]}).sort_values(x)
    fig = px.line(df, x=x, y=y, title=f'{y} plot', labels={x: x, y: y})
    fig.add_trace(px.scatter(df, x=x, y=y).data[0])
    st.plotly_chart(fig)


def process_table(data_manager, category, title, report, is_column, main_column_flag):
    match = get_information_dataframe(data_manager, category, title, report)
    print(match)
    freq_column = None
    if not is_column:
        units_id = None
        for match_column in match.columns:
            for id_row, val in match[match_column].items():
                if main_column_flag in str(val):
                    freq_column = match_column
                    units_id = id_row
                    break
            if units_id is not None:
                break

        if freq_column:
            print(units_id)
            units_row = match.loc[units_id]
            new_columns = [f"{col} ({unit})" if unit and col not in ['Fecha extracción', freq_column] else col
                           for col, unit in zip(match.columns, units_row)]
            match.columns = new_columns
    else:
        if main_column_flag in match.columns:
            freq_column = main_column_flag

    final_table = pd.DataFrame()
    for match_column in match.columns:
        if 'Fecha' in match_column:
            new_table = data_manager.modify_table(match, match_column, 'date')
        else:
            new_table = data_manager.modify_table(match, match_column, 'numeric')
        if not new_table.empty:
            final_table[match_column] = new_table[match_column]
    last_date = final_table['Fecha extracción'].max()
    final_table = final_table[final_table['Fecha extracción'] == last_date]
    return final_table, freq_column


def get_information_dataframe(data_manager, category, title, well_name):
    categories_list = data_manager.get_categories()
    defined_category = next((element for element in categories_list if category in element), None)
    data = data_manager.get_stored_table(defined_category, True, title, 'Pozo', False, well_name)
    return data


st.set_page_config(layout='wide', initial_sidebar_state='collapsed')
st.markdown(f'### Dashboards')
dm = DataManager(st.session_state.user['uid'], st.session_state.user['email'], f'db_collection')
try:
    selection = st.selectbox('Wells:', get_well_names(dm))
    general_difa = get_information_dataframe(dm, 'DIFA', 'general', selection)
    fecha_reciente = general_difa['Fecha extracción'].max()
    general_difa = general_difa[general_difa['Fecha extracción'] == fecha_reciente]
    general_difa = general_difa.drop('Fecha extracción', axis=1)
    general_columns = st.columns(len(general_difa.columns))
    Extras.change_metric_style(20)
    for i, column in enumerate(general_difa.columns):
        values = general_difa[column][0]
        general_columns[i].metric(column, values)
except Exception as e:
    print(e)
    st.caption('No data was extracted or there is no data to show')

c1, c2 = st.columns(2)
bomba_eff, motor_eff = st.columns(2)

# Primera vista - Datos de Pull
with c1:
    try:
        titles_pull = Extras.get_attributes_names('table')['Pull']
        if 'Observaciones' in titles_pull:
            titles_pull.remove('Observaciones')
        print(titles_pull)
        st.markdown(f'### Pull')
        for titles in titles_pull:
            st.markdown(f'###### {titles}')
            st.write(get_information_dataframe(dm, 'Pull', titles, selection))
    except Exception as e:
        print(e)
        st.caption('No data was extracted or there is no data to show')

with c2:
    try:
        # segunda vista - Antecedentes DIFA
        st.markdown(f'### DIFA')
        st.markdown(f'##### Antecedentes')
        st.write(get_information_dataframe(dm, 'DIFA', 'Antecedentes', selection))

        st.markdown(f'##### Eventos')
        st.write(get_information_dataframe(dm, 'DIFA', 'Eventos', selection))

        # tercera vista - Hallazgos TD
        titles_pull = Extras.get_attributes_names('table')['Tear Down']
        hallazgos = pd.DataFrame()
        print(titles_pull)
        for titles in titles_pull:
            hallazgos = pd.concat([hallazgos, get_information_dataframe(dm, 'Tear Down', titles, selection)])

        st.markdown(f'### Tear Down')
        st.write(hallazgos)
    except Exception as e:
        print(e)
        st.caption('No data was extracted or there is no data to show')

# cuarta vista - Bomba Match
with bomba_eff:
    try:
        final_bomba, freq_column_bomba = process_table(dm, 'Matching',
                                                       'Bomba-tr', selection, False, 'Units')

        st.markdown(f'### Match')
        st.markdown(f'##### Bomba')
        # obtencion de parametros importantes para ver rendimiento
        select_pump = []
        for column in final_bomba.columns:
            if final_bomba[column].dtype == 'datetime64[ns]':
                # Eliminar la columna si es de tipo 'datetime64'
                final_bomba.drop(column, axis=1, inplace=True)
            elif final_bomba[column].dtype in ['float64', 'int64'] and column != freq_column_bomba:
                # Agregar el nombre de la columna si es numérica
                select_pump.append(column)
        select_options_pump = st.selectbox('Metric to plot:', select_pump, key='pump_options')
        plot_series(freq_column_bomba, select_options_pump, final_bomba)

        st.write(final_bomba)
    except Exception as e:
        print(e)
        st.caption('No data was extracted or there is no data to show')

# quinta vista - Motor Match
with motor_eff:
    try:
        final_motor, freq_column_motor = process_table(dm, 'Matching',
                                                       'Motor-tr', selection, False, 'Units')

        st.markdown(f'### Match')
        st.markdown(f'##### Motor')
        # obtencion de parametros importantes para ver rendimiento
        selectbox_motor = []
        for column in final_motor.columns:
            if final_motor[column].dtype == 'datetime64[ns]':
                # Eliminar la columna si es de tipo 'datetime64'
                final_motor.drop(column, axis=1, inplace=True)
            elif final_motor[column].dtype in ['float64', 'int64'] and column != freq_column_motor:
                # Agregar el nombre de la columna si es numérica
                selectbox_motor.append(column)
        select_options_motor = st.selectbox('Metric to plot:', selectbox_motor, key='motor_options')
        plot_series(freq_column_motor, select_options_motor, final_motor)

        st.write(final_motor)
    except Exception as e:
        print(e)
        st.caption('No data was extracted or there is no data to show')

# sexta vista - produccion DIFA
try:
    final_produccion, freq_column_prod = process_table(dm, 'DIFA',
                                                       'Producción', selection, True, 'Fecha')

    st.markdown(f'### DIFA')
    st.markdown(f'##### Producción')
    # obtencion de parametros importantes para ver rendimiento
    select_prod = []
    for column in final_produccion.columns:
        if final_produccion[column].dtype == 'datetime64[ns]' and column != freq_column_prod:
            # Eliminar la columna si es de tipo 'datetime64'
            final_produccion.drop(column, axis=1, inplace=True)
        elif final_produccion[column].dtype in ['float64', 'int64'] and column != freq_column_prod:
            # Agregar el nombre de la columna si es numérica
            select_prod.append(column)
    select_options_prod = st.selectbox('Metric to plot:', select_prod, key='prod_options')
    plot_series(freq_column_prod, select_options_prod, final_produccion)

    st.write(final_produccion)
except Exception as e:
    print(e)
    st.caption('No data was extracted or there is no data to show')
