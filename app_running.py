import pandas as pd
import os
import numpy as np
import streamlit as st
from scipy.stats import poisson
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
from streamlit_option_menu import option_menu
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from vega_datasets import data
import plotly.express as px
from datetime import datetime


#Pagina
st.set_page_config(layout="wide")

# Conexión con Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
#creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales_running.json", scope)
cred_dict = st.secrets["gcp_service_account"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(cred_dict,scope)
client = gspread.authorize(credentials)


#Iniciar sesión
st.header(':green[Iniciar sesión]')
usuarios = {
    "Daves": "runner9306",
    "Gasca": "runner6202",
    "Diegsta" : "runner9805"
}

if "logueado" not in st.session_state:
    st.session_state.logueado = False

# Solo mostrar login si no está logueado
if not st.session_state.logueado:
    usuario = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Iniciar sesión"):
        if usuario in usuarios and usuarios[usuario] == password:
            st.session_state.logueado = True
            st.session_state.usuario = usuario  # Guardamos el nombre si lo necesitas
            st.success(f"Bienvenido, {usuario} 👋")
            st.rerun()  # 🔄 Esto fuerza que se recargue la app con el estado actualizado
        else:
            st.error("Usuario o contraseña incorrectos ❌")
else:
    st.success(f"Bienvenido, {st.session_state.usuario} 👋")

    #menu
    selected = option_menu(
        menu_title = 'Corredor',
        options = ['David M. G.','David M. L.','Diego M. L.'],   
        styles = {
            "nav-link":{"font-size": "11px",
            "text-align": "left" }
        },
        menu_icon= "cast",
        default_index=0,
        orientation="horizontal"
    )


    #Diego
    hoja_diego = client.open("Running").worksheet("Diego")
    df_diego = pd.DataFrame(hoja_diego.get_all_records())

    #DMG
    hoja_dmg = client.open("Run_dmg").worksheet("DMG")
    df_dmg = pd.DataFrame(hoja_dmg.get_all_records())

    #Daves
    hoja_daves = client.open("Run_dmarlop").worksheet("Data")
    df_daves = pd.DataFrame(hoja_daves.get_all_records())



    if selected == 'David M. G.':
        #Meses
        df_dmg['Fecha'] = pd.to_datetime(df_dmg['Fecha'], format='%d/%m/%Y')
        df_dmg['Mes'] = df_dmg['Fecha'].dt.strftime('%b')   
        df_dmg['Año'] = df_dmg['Fecha'].dt.year 
        meses_orden = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        # Extraer años únicos ordenados
        anios_disponibles = sorted(df_dmg['Año'].unique(), reverse=True)

        # Filtro de selección de año
        anios_disponibles_con_todos = ["Todos"] + anios_disponibles

        anio_seleccionado = st.selectbox("Selecciona un año:", anios_disponibles_con_todos)


        # Filtrar según selección
        if anio_seleccionado == "Todos":
            df_dmg_filtrado = df_dmg.copy()
        else:
            df_dmg_filtrado = df_dmg[df_dmg['Año'] == anio_seleccionado]



        #st.header("Datos DMG")
        #st.dataframe(df_dmg_filtrado)

        
        #kilometros
        kms_dmg = round(df_dmg_filtrado['Kilometros'].sum(),2)
        df_km_dmg = df_dmg_filtrado.groupby('Año', as_index=False)['Kilometros'].sum()
        df_km_dmg_mes = df_dmg_filtrado.groupby('Mes', as_index=False)['Kilometros'].sum()
        df_km_dmg_mes['Mes'] = pd.Categorical(df_km_dmg_mes['Mes'], categories=meses_orden, ordered=True)
        #Tiempo
        df_dmg_filtrado['Tiempo'] = pd.to_timedelta(df_dmg_filtrado['Tiempo'])
        tiempo_dmg = df_dmg_filtrado['Tiempo'].sum()
        total_str = str(tiempo_dmg)
        horas_totales = tiempo_dmg.total_seconds() / 3600

        # Calcular velocidad promedio
        if horas_totales > 0:
            velocidad_promedio = kms_dmg / horas_totales
        else:
            velocidad_promedio = 0

        df_dmg['Tiempo'] = pd.to_timedelta(df_dmg['Tiempo'])

        df_tiempo_promedio = df_dmg.groupby('Año').agg({
        'Kilometros': 'sum',
        'Tiempo': 'sum'
        }).reset_index()

        # Calcular segundos por km
        df_tiempo_promedio['Tiempo_promedio_seg'] = df_tiempo_promedio['Tiempo'].dt.total_seconds() / df_tiempo_promedio['Kilometros']

        # Convertir a formato timedelta
        df_tiempo_promedio['Tiempo promedio por km'] = pd.to_timedelta(df_tiempo_promedio['Tiempo_promedio_seg'], unit='s')


        df_resultado = df_tiempo_promedio[['Año', 'Kilometros', 'Tiempo promedio por km']].rename(columns={
        'Kilometros': 'Km totales'
        })

        df_resultado['Tiempo promedio por km'] = df_resultado['Tiempo promedio por km'].apply(
        lambda x: f"{int(x.total_seconds() // 60):02d}:{int(x.total_seconds() % 60):02d} min" if pd.notnull(x) else "-"
        )

        #Entorno
        df_entorno_dmg = df_dmg_filtrado.groupby('Entorno', as_index=False)['Kilometros'].sum()
        color_map = {
        'Interior': '#00927c',
        'Exterior': '#f4a261'
                    }
        
        #Comparar meses
        df_meses_vs_anios = df_dmg.groupby(['Mes', 'Año'], as_index=False)['Kilometros'].sum()

        # Asegurar orden correcto de meses
        df_meses_vs_anios['Mes'] = pd.Categorical(df_meses_vs_anios['Mes'], categories=meses_orden, ordered=True)
        df_meses_vs_anios = df_meses_vs_anios.sort_values(['Mes', 'Año'])
        
        with st.container(border=True):
            col1, col2,col3  = st.columns(3)
            with col1:
                st.metric(label='Kms 🏃‍♂️📏',value=kms_dmg)
            with col2:
                st.metric(label='Tiempo ⌚',value=total_str)
            with col3:
                st.metric(label="Velocidad promedio 🚴‍♂️", value=f"{velocidad_promedio:.2f} km/h")
        
        with st.container(border=True):
            col1,col2 = st.columns(2)
            with col1:
                st.subheader("Kms por año")
                st.bar_chart(df_km_dmg.set_index('Año')['Kilometros'], color="#00927c")
            with col2:
                st.subheader("Kms por mes")
                df_km_dmg_mes = df_km_dmg_mes.sort_values('Mes')
                st.bar_chart(df_km_dmg_mes.set_index('Mes')['Kilometros'], color="#00927c")
            col3, = st.columns(1)
            with col3:
                fig = px.pie(
                df_entorno_dmg,                # Tu DataFrame ya agrupado
                names='Entorno',               # Columna para las etiquetas
                values='Kilometros',           # Columna con los valores numéricos
                title='Kilometros por entorno',
                color='Entorno',
                color_discrete_map=color_map 
                )
                st.plotly_chart(fig)
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Comparativa kms por meses y año")
                tabla_pivote = df_meses_vs_anios.pivot(index='Mes', columns='Año', values='Kilometros')
                st.dataframe(tabla_pivote)
            with col2:
                st.subheader("🕒 Tiempo promedio por kilómetro")
                st.dataframe(df_resultado)

        
    if selected == 'Diego M. L.':
        #st.header("Datos Diego")
        #st.dataframe(df_diego)


        #Meses
        df_diego['Fecha'] = pd.to_datetime(df_diego['Fecha'], format='%d/%m/%Y')
        df_diego['Mes'] = df_diego['Fecha'].dt.strftime('%b')   
        df_diego['Año'] = df_diego['Fecha'].dt.year 
        meses_orden = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        # Extraer años únicos ordenados
        anios_disponibles = sorted(df_diego['Año'].unique(), reverse=True)

        # Filtro de selección de año
        anios_disponibles_con_todos = ["Todos"] + anios_disponibles

        anio_seleccionado = st.selectbox("Selecciona un año:", anios_disponibles_con_todos)


        # Filtrar según selección
        if anio_seleccionado == "Todos":
            df_diego_filtrado = df_diego.copy()
        else:
            df_diego_filtrado = df_diego[df_diego['Año'] == anio_seleccionado]



        #st.header("Datos DMG")
        #st.dataframe(df_diego_filtrado)

        
        #kilometros
        kms_diego = round(df_diego_filtrado['Kilometros'].sum(),2)
        df_km_diego = df_diego_filtrado.groupby('Año', as_index=False)['Kilometros'].sum()
        df_km_diego_mes = df_diego_filtrado.groupby('Mes', as_index=False)['Kilometros'].sum()
        df_km_diego_mes['Mes'] = pd.Categorical(df_km_diego_mes['Mes'], categories=meses_orden, ordered=True)
        #Tiempo
        df_diego_filtrado['Tiempo'] = pd.to_timedelta(df_diego_filtrado['Tiempo'])
        tiempo_diego = df_diego_filtrado['Tiempo'].sum()
        total_str = str(tiempo_diego)
        horas_totales = tiempo_diego.total_seconds() / 3600

        # Calcular velocidad promedio
        if horas_totales > 0:
            velocidad_promedio = kms_diego / horas_totales
        else:
            velocidad_promedio = 0

        df_diego['Tiempo'] = pd.to_timedelta(df_diego['Tiempo'])

        df_tiempo_promedio = df_diego.groupby('Año').agg({
        'Kilometros': 'sum',
        'Tiempo': 'sum'
        }).reset_index()

        # Calcular segundos por km
        df_tiempo_promedio['Tiempo_promedio_seg'] = df_tiempo_promedio['Tiempo'].dt.total_seconds() / df_tiempo_promedio['Kilometros']

        # Convertir a formato timedelta
        df_tiempo_promedio['Tiempo promedio por km'] = pd.to_timedelta(df_tiempo_promedio['Tiempo_promedio_seg'], unit='s')


        df_resultado = df_tiempo_promedio[['Año', 'Kilometros', 'Tiempo promedio por km']].rename(columns={
        'Kilometros': 'Km totales'
        })

        df_resultado['Tiempo promedio por km'] = df_resultado['Tiempo promedio por km'].apply(
        lambda x: f"{int(x.total_seconds() // 60):02d}:{int(x.total_seconds() % 60):02d} min" if pd.notnull(x) else "-"
        )

        #Entorno
        df_entorno_diego = df_diego_filtrado.groupby('Entorno', as_index=False)['Kilometros'].sum()
        color_map = {
        'Interior': '#a50044',
        'Exterior': '#004d98'
                    }
        
        #Comparar meses
        df_meses_vs_anios = df_diego.groupby(['Mes', 'Año'], as_index=False)['Kilometros'].sum()

        # Asegurar orden correcto de meses
        df_meses_vs_anios['Mes'] = pd.Categorical(df_meses_vs_anios['Mes'], categories=meses_orden, ordered=True)
        df_meses_vs_anios = df_meses_vs_anios.sort_values(['Mes', 'Año'])
        
        with st.container(border=True):
            col1, col2,col3  = st.columns(3)
            with col1:
                st.metric(label='Kms 🏃‍♂️📏',value=kms_diego)
            with col2:
                st.metric(label='Tiempo ⌚',value=total_str)
            with col3:
                st.metric(label="Velocidad promedio 🚴‍♂️", value=f"{velocidad_promedio:.2f} km/h")
        
        with st.container(border=True):
            col1,col2 = st.columns(2)
            with col1:
                st.subheader("Kms por año")
                st.bar_chart(df_km_diego.set_index('Año')['Kilometros'], color="#004d98")
            with col2:
                st.subheader("Kms por mes")
                df_km_diego_mes = df_km_diego_mes.sort_values('Mes')
                st.bar_chart(df_km_diego_mes.set_index('Mes')['Kilometros'], color="#004d98")
            col3, = st.columns(1)
            with col3:
                fig = px.pie(
                df_entorno_diego,                # Tu DataFrame ya agrupado
                names='Entorno',               # Columna para las etiquetas
                values='Kilometros',           # Columna con los valores numéricos
                title='Kilometros por entorno',
                color='Entorno',
                color_discrete_map=color_map 
                )
                st.plotly_chart(fig)
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Comparativa kms por meses y año")
                tabla_pivote = df_meses_vs_anios.pivot(index='Mes', columns='Año', values='Kilometros')
                st.dataframe(tabla_pivote)
            with col2:
                st.subheader("🕒 Tiempo promedio por kilómetro")
                st.dataframe(df_resultado)




    if selected == 'David M. L.':
        #st.header("Datos Daves")
        #st.dataframe(df_daves)

        #Meses
        df_daves['Fecha'] = pd.to_datetime(df_daves['Fecha'], format='%d/%m/%Y')
        df_daves['Mes'] = df_daves['Fecha'].dt.strftime('%b')   
        df_daves['Año'] = df_daves['Fecha'].dt.year 
        meses_orden = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        # Extraer años únicos ordenados
        anios_disponibles = sorted(df_daves['Año'].unique(), reverse=True)

        # Filtro de selección de año
        anios_disponibles_con_todos = ["Todos"] + anios_disponibles

        anio_seleccionado = st.selectbox("Selecciona un año:", anios_disponibles_con_todos)


        # Filtrar según selección
        if anio_seleccionado == "Todos":
            df_daves_filtrado = df_daves.copy()
        else:
            df_daves_filtrado = df_daves[df_daves['Año'] == anio_seleccionado]



        #st.header("Datos DMG")
        #st.dataframe(df_diego_filtrado)

        
        #kilometros
        kms_daves = round(df_daves_filtrado['Kilometros'].sum(),2)
        df_km_daves = df_daves_filtrado.groupby('Año', as_index=False)['Kilometros'].sum()
        df_km_daves_mes = df_daves_filtrado.groupby('Mes', as_index=False)['Kilometros'].sum()
        df_km_daves_mes['Mes'] = pd.Categorical(df_km_daves_mes['Mes'], categories=meses_orden, ordered=True)
        #Tiempo
        df_daves_filtrado['Tiempo'] = pd.to_timedelta(df_daves_filtrado['Tiempo'])
        tiempo_daves = df_daves_filtrado['Tiempo'].sum()
        total_str = str(tiempo_daves)
        horas_totales = tiempo_daves.total_seconds() / 3600

        # Calcular velocidad promedio
        if horas_totales > 0:
            velocidad_promedio = kms_daves / horas_totales
        else:
            velocidad_promedio = 0

        df_daves['Tiempo'] = pd.to_timedelta(df_daves['Tiempo'])

        df_tiempo_promedio = df_daves.groupby('Año').agg({
        'Kilometros': 'sum',
        'Tiempo': 'sum'
        }).reset_index()

        # Calcular segundos por km
        df_tiempo_promedio['Tiempo_promedio_seg'] = df_tiempo_promedio['Tiempo'].dt.total_seconds() / df_tiempo_promedio['Kilometros']

        # Convertir a formato timedelta
        df_tiempo_promedio['Tiempo promedio por km'] = pd.to_timedelta(df_tiempo_promedio['Tiempo_promedio_seg'], unit='s')


        df_resultado = df_tiempo_promedio[['Año', 'Kilometros', 'Tiempo promedio por km']].rename(columns={
        'Kilometros': 'Km totales'
        })

        df_resultado['Tiempo promedio por km'] = df_resultado['Tiempo promedio por km'].apply(
        lambda x: f"{int(x.total_seconds() // 60):02d}:{int(x.total_seconds() % 60):02d} min" if pd.notnull(x) else "-"
        )

        #Entorno
        df_entorno_daves = df_daves_filtrado.groupby('Entorno', as_index=False)['Kilometros'].sum()
        color_map = {
        'Interior': '#F54927',
        'Exterior': '#F5B027'
                    }
        
        #Comparar meses
        df_meses_vs_anios = df_daves.groupby(['Mes', 'Año'], as_index=False)['Kilometros'].sum()

        # Asegurar orden correcto de meses
        df_meses_vs_anios['Mes'] = pd.Categorical(df_meses_vs_anios['Mes'], categories=meses_orden, ordered=True)
        df_meses_vs_anios = df_meses_vs_anios.sort_values(['Mes', 'Año'])
        
        with st.container(border=True):
            col1, col2,col3  = st.columns(3)
            with col1:
                st.metric(label='Kms 🏃‍♂️📏',value=kms_daves)
            with col2:
                st.metric(label='Tiempo ⌚',value=total_str)
            with col3:
                st.metric(label="Velocidad promedio 🚴‍♂️", value=f"{velocidad_promedio:.2f} km/h")
        
        with st.container(border=True):
            col1,col2 = st.columns(2)
            with col1:
                st.subheader("Kms por año")
                st.bar_chart(df_km_daves.set_index('Año')['Kilometros'], color="#F54927")
            with col2:
                st.subheader("Kms por mes")
                df_km_daves_mes = df_km_daves_mes.sort_values('Mes')
                st.bar_chart(df_km_daves_mes.set_index('Mes')['Kilometros'], color="#F54927")
            col3, = st.columns(1)
            with col3:
                fig = px.pie(
                df_entorno_daves,                # Tu DataFrame ya agrupado
                names='Entorno',               # Columna para las etiquetas
                values='Kilometros',           # Columna con los valores numéricos
                title='Kilometros por entorno',
                color='Entorno',
                color_discrete_map=color_map 
                )
                st.plotly_chart(fig)
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Comparativa kms por meses y año")
                tabla_pivote = df_meses_vs_anios.pivot(index='Mes', columns='Año', values='Kilometros')
                st.dataframe(tabla_pivote)
            with col2:
                st.subheader("🕒 Tiempo promedio por kilómetro")
                st.dataframe(df_resultado)






