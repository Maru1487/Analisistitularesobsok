import streamlit as st
import pandas as pd

st.set_page_config(page_title="Análisis automatizado de titulares", layout="wide")

st.title("Análisis automatizado de titulares de El Observador")
st.write("Subí dos archivos CSV exportados de Marfeel: uno con el total de lecturas y otro con las fuentes de tráfico.")

# 1. SUBIDA DE ARCHIVOS
csv1 = st.file_uploader("Archivo 1: Pageviews totales", type="csv", key="csv1")
csv2 = st.file_uploader("Archivo 2: Pageviews por fuente de tráfico", type="csv", key="csv2")

if csv1 and csv2:
    # 2. LEER Y NORMALIZAR
    df1 = pd.read_csv(csv1)
    df2 = pd.read_csv(csv2)
    df1.columns = df1.columns.str.strip().str.lower().str.replace(" ", "_")
    df2.columns = df2.columns.str.strip().str.lower().str.replace(" ", "_")

    # 3. DETERMINAR CUÁL ES CUÁL
    if 'sourceinternal' in df1.columns:
        df_fuentes = df1
        df_totales = df2
    else:
        df_fuentes = df2
        df_totales = df1

    # 4. AGRUPAR Y DETECTAR FUENTE PRINCIPAL
    df_fuentes_agg = df_fuentes.groupby(['title', 'sourceinternal'])['pageviewstotal'].sum().reset_index()
    idx_max = df_fuentes_agg.groupby('title')['pageviewstotal'].idxmax()
    df_fuente_principal = df_fuentes_agg.loc[idx_max].reset_index(drop=True)
    df_fuente_principal = df_fuente_principal.rename(columns={
        'pageviewstotal': 'pageviews_fuente_principal',
        'sourceinternal': 'fuente_principal'
    })

    # 5. UNIR Y CALCULAR PORCENTAJE
    df_final = pd.merge(df_totales, df_fuente_principal, on='title', how='left')
    df_final['porcentaje_fuente_principal'] = (
        df_final['pageviews_fuente_principal'] / df_final['pageviewstotal'] * 100
    ).round(2)

    # 6. RENOMBRAR ENCABEZADOS PARA VISUALIZACIÓN
    resultado = df_final[['title', 'pageviewstotal', 'fuente_principal', 'porcentaje_fuente_principal']]
    resultado = resultado.sort_values(by='pageviewstotal', ascending=False).reset_index(drop=True)
    resultado_mostrar = resultado.rename(columns={
        'title': 'Título',
        'pageviewstotal': 'Total de pageviews',
        'fuente_principal': 'Fuente principal',
        'porcentaje_fuente_principal': 'Porcentaje de la fuente principal'
    })

    # 7. FILTRO TEMÁTICO
    st.subheader("Filtrar títulos por palabra clave")
    palabra_clave = st.text_input("Ingresá una palabra o expresión para filtrar títulos:", "")

    if palabra_clave:
import re

# Solo si el campo de texto NO está vacío
if palabra_clave.strip():
    # Usamos \b para buscar la palabra exacta
    patron = r"\b" + re.escape(palabra_clave.strip()) + r"\b"
    resultado_filtrado = resultado_mostrar[resultado_mostrar['Título'].str.contains(patron, case=False, na=False, regex=True)]
else:
    resultado_filtrado = resultado_mostrar
    
    st.dataframe(resultado_filtrado.head(20), use_container_width=True)

else:
    st.info("Esperando que subas ambos archivos CSV para mostrar los resultados.")
