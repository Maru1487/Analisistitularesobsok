import streamlit as st
import pandas as pd

st.title("Análisis de titulares de El Observador")

st.write("Subí dos archivos CSV exportados de Marfeel para comenzar.")

archivos = st.file_uploader(
    "Elegí dos archivos CSV", type="csv", accept_multiple_files=True
)

def normalizar_columnas(df):
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    return df

if archivos and len(archivos) == 2:
    # Leer y normalizar
    df1 = pd.read_csv(archivos[0])
    df2 = pd.read_csv(archivos[1])
    df1 = normalizar_columnas(df1)
    df2 = normalizar_columnas(df2)

    # Inferir cuál es cuál
    if 'sourceinternal' in df1.columns:
        df_fuentes = df1
        df_totales = df2
    else:
        df_fuentes = df2
        df_totales = df1

    # Agrupar fuentes de tráfico
    df_fuentes_agg = df_fuentes.groupby(['title', 'sourceinternal'])['pageviewstotal'].sum().reset_index()
    # Identificar fuente principal
    idx_max = df_fuentes_agg.groupby('title')['pageviewstotal'].idxmax()
    df_fuente_principal = df_fuentes_agg.loc[idx_max].reset_index(drop=True)
    df_fuente_principal = df_fuente_principal.rename(columns={
        'pageviewstotal': 'pageviews_fuente_principal',
        'sourceinternal': 'fuente_principal'
    })
    # Unir con totales
    df_final = pd.merge(df_totales, df_fuente_principal, on='title', how='left')
    # Calcular porcentaje
    df_final['porcentaje_fuente_principal'] = (
        df_final['pageviews_fuente_principal'] / df_final['pageviewstotal'] * 100
    ).round(2)

    # Resultado ordenado
    resultado = df_final[['title', 'pageviewstotal', 'fuente_principal', 'porcentaje_fuente_principal']]
    resultado = resultado.sort_values(by='pageviewstotal', ascending=False).reset_index(drop=True)

    st.success("Análisis generado correctamente. Tabla principal:")
    st.dataframe(resultado.head(30))
else:
    if archivos and len(archivos) != 2:
        st.error("Debés subir exactamente DOS archivos.")
