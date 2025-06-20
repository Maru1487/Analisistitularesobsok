import streamlit as st
import pandas as pd

st.title("Análisis de titulares de El Observador")

st.write("Subí dos archivos CSV exportados de Marfeel para comenzar.")

archivos = st.file_uploader(
    "Elegí dos archivos CSV", type="csv", accept_multiple_files=True
)

if archivos and len(archivos) == 2:
    st.success("Archivos subidos correctamente.")
    # Mostrar nombres
    st.write("Archivos:", [a.name for a in archivos])
    # Previsualizar los primeros 10 registros de ambos
    for idx, archivo in enumerate(archivos):
        df = pd.read_csv(archivo)
        st.write(f"Vista previa de {archivo.name}:")
        st.dataframe(df.head(10))
elif archivos and len(archivos) != 2:
    st.error("Debés subir exactamente DOS archivos.")
