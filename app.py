import streamlit as st
import pandas as pd
import spacy
import re
import matplotlib.pyplot as plt
import plotly.express as px

# --- ENTIDADES Y VERBOS ---
entidades_locales_uy = [
    "IRPF", "BPS", "DGI", "AFAP", "ANEP", "CODICEN", "UTE", "OSE", "ANTEL", "MIDES",
    "MGAP", "MEF", "MEC", "MI", "MSP", "MTOP", "MRREE", "INAU", "INISA",
    "FA", "PN", "PC", "CA", "TC", "SCJ", "IMM", "BHU", "BROU", "Banco República",
    "FONASA", "SNIC", "UTU", "Universidad de la República", "Udelar", "ANV", "ANCAP",
    "INE", "INUMET", "IMPO", "PIT-CNT", "SIIAS", "CNCS", "SMU", "ASSE", "SUINAU",
    "Sunca", "Conaprole", "COFE", "CUTCSA", "IASS", "MIEM", "MTSS", "FFAA", "FAU",
    "ANP", "TCR", "INDDHH", "AUF", "COPSA", "TCA", "PJ", "PE", "TOCAF"
]
verbos_declarativos = [
    "anunció", "anunciará", "confirmó", "confirmará", "decidió", "decidirá", 
    "rechazó", "rechazará", "defendió", "defenderá", "cuestionó", "cuestionará",
    "propuso", "propondrá", "sostuvo", "sostendrá", "denunció", "denunciará", 
    "convocó", "convocará", "presentó", "presentará", "pidió", "pedirá",
    "apoyó", "apoyará", "criticó", "criticarán", "celebró", "celebrará"
]

# --- CARGA DE MODELO SPACY ---
import spacy
nlp = spacy.load("es_core_news_sm")

# --- FUNCIONES ---
def extraer_entidades(titulo):
    doc = nlp(titulo)
    entidades_spacy = [ent.text for ent in doc.ents if ent.label_ in ("PER", "ORG", "LOC")]
    entidades_locales_encontradas = []
    palabras = re.findall(r'\b[A-ZÁÉÍÓÚÑ]{2,}\b', titulo)
    for ent in entidades_locales_uy:
        if any(ent == p for p in palabras):
            entidades_locales_encontradas.append(ent)
        elif ent.lower() in titulo.lower() and " " in ent:
            entidades_locales_encontradas.append(ent)
    return list(set(entidades_spacy + entidades_locales_encontradas))

def detectar_tono(titulo):
    interrogativos = ["qué", "quién", "quiénes", "cuándo", "cómo", "dónde", "cuál", "cuáles", "por qué", "para qué"]
    exclamativos = ["insólito", "sorprendente", "impresionante", "increíble", "dramático", "emotivo", "desgarrador", "escándalo", "¡atención!", "alerta", "brutal", "impactante"]
    titulo_l = titulo.lower()
    if any(sign in titulo for sign in ("¿", "?")) or any(titulo_l.startswith(p+" ") for p in interrogativos):
        return "interrogativo"
    if any(sign in titulo for sign in ("¡", "!")) or any(exp in titulo_l for exp in exclamativos):
        return "exclamativo"
    return "neutro"

def tiene_cita(titulo):
    return "sí" if re.search(r'["“”]', titulo) else "no"

def posicion_entidad(titulo, entidades):
    if not entidades:
        return "sin_entidad"
    entidad = entidades[0]
    idx = titulo.lower().find(entidad.lower())
    if idx == -1:
        return "sin_entidad"
    porc = idx / max(len(titulo), 1)
    if porc < 0.2:
        return "inicio"
    elif porc > 0.7:
        return "final"
    else:
        return "medio"

def determinar_estilo(titulo, entidades):
    doc = nlp(titulo)
    tokens = [t.text.lower() for t in doc]
    lemmas = [t.lemma_.lower() for t in doc]
    verbos = [t for t in doc if t.pos_ == "VERB"]
    if verbos and entidades:
        return "narrativo"
    if any(v in tokens or v in lemmas for v in verbos_declarativos) and entidades:
        return "declarativo"
    return "informativo-descriptivo"

def numeros_texto():
    return set([
        "uno", "una", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez", "once", "doce", "trece", "catorce",
        "quince", "dieciséis", "diecisiete", "dieciocho", "diecinueve", "veinte", "treinta", "cuarenta", "cincuenta", "sesenta",
        "setenta", "ochenta", "noventa", "cien", "ciento", "doscientos", "mil", "millón", "billón"
    ])
def analizar_numeros(titulo):
    digitos = re.findall(r'\d+', titulo)
    txt = set(titulo.lower().split())
    texto_n = numeros_texto()
    hay_txt = txt.intersection(texto_n)
    if digitos and hay_txt:
        return "ambos"
    if digitos:
        return "número_dígito"
    if hay_txt:
        return "número_texto"
    return "ninguno"

def tiene_numeros(titulo):
    return "sí" if re.search(r'\d', titulo) or set(titulo.lower().split()).intersection(numeros_texto()) else "no"

def cantidad_numeros(titulo):
    return len(re.findall(r'\d+', titulo)) + len(set(titulo.lower().split()).intersection(numeros_texto()))

# --- APP STREAMLIT ---
st.set_page_config(page_title="Análisis automatizado de titulares", layout="wide")
st.title("Análisis automatizado de titulares de El Observador")
st.write("Subí dos archivos CSV exportados de Marfeel: uno con el total de lecturas y otro con las fuentes de tráfico.")

csv1 = st.file_uploader("Archivo 1: Pageviews totales", type="csv", key="csv1")
csv2 = st.file_uploader("Archivo 2: Pageviews por fuente de tráfico", type="csv", key="csv2")

if csv1 and csv2:
    df1 = pd.read_csv(csv1)
    df2 = pd.read_csv(csv2)
    df1.columns = df1.columns.str.strip().str.lower().str.replace(" ", "_")
    df2.columns = df2.columns.str.strip().str.lower().str.replace(" ", "_")
    if 'sourceinternal' in df1.columns:
        df_fuentes = df1
        df_totales = df2
    else:
        df_fuentes = df2
        df_totales = df1

    df_fuentes_agg = df_fuentes.groupby(['title', 'sourceinternal'])['pageviewstotal'].sum().reset_index()
    idx_max = df_fuentes_agg.groupby('title')['pageviewstotal'].idxmax()
    df_fuente_principal = df_fuentes_agg.loc[idx_max].reset_index(drop=True)
    df_fuente_principal = df_fuente_principal.rename(columns={
        'pageviewstotal': 'pageviews_fuente_principal',
        'sourceinternal': 'fuente_principal'
    })

    df_final = pd.merge(df_totales, df_fuente_principal, on='title', how='left')
    df_final['porcentaje_fuente_principal'] = (
        df_final['pageviews_fuente_principal'] / df_final['pageviewstotal'] * 100
    ).round(2)
    resultado = df_final[['title', 'pageviewstotal', 'fuente_principal', 'porcentaje_fuente_principal']]
    resultado = resultado.sort_values(by='pageviewstotal', ascending=False).reset_index(drop=True)

    # --- ANÁLISIS SINTÁCTICO AVANZADO ---
    resultado['longitud_titulo'] = resultado['title'].apply(len)
    resultado['entidades'] = resultado['title'].apply(extraer_entidades)
    resultado['¿Tiene entidades?'] = resultado['entidades'].apply(lambda x: "sí" if len(x) > 0 else "no")
    resultado['Cantidad de entidades'] = resultado['entidades'].apply(len)
    resultado['Tono'] = resultado['title'].apply(detectar_tono)
    resultado['¿Cita?'] = resultado['title'].apply(tiene_cita)
    resultado['Posición entidad'] = resultado.apply(lambda row: posicion_entidad(row['title'], row['entidades']), axis=1)
    resultado['Estilo'] = resultado.apply(lambda row: determinar_estilo(row['title'], row['entidades']), axis=1)
    resultado['Formato numérico'] = resultado['title'].apply(analizar_numeros)
    resultado['¿Tiene números?'] = resultado['title'].apply(tiene_numeros)
    resultado['Cantidad de números'] = resultado['title'].apply(cantidad_numeros)

    # --- RENOMBRAR ENCABEZADOS ---
    resultado_mostrar = resultado.rename(columns={
        'title': 'Título',
        'pageviewstotal': 'Total de pageviews',
        'fuente_principal': 'Fuente principal',
        'porcentaje_fuente_principal': 'Porcentaje de la fuente principal',
        'longitud_titulo': 'Extensión',
        'entidades': 'Entidades',
        # Los demás campos ya están en español
    })

    # --- TABLA PRINCIPAL ---
    st.subheader("Tabla principal: todas las variables de análisis sintáctico")
    st.dataframe(resultado_mostrar.head(30), use_container_width=True)

    # --- FILTRO TEMÁTICO ROBUSTO ---
    st.subheader("Filtrar títulos por palabra clave (palabra exacta)")
    palabra_clave = st.text_input("Ingresá una palabra o expresión exacta para filtrar títulos (distingue palabra aislada):", "")
    if palabra_clave:
        regex = r'\b{}\b'.format(re.escape(palabra_clave.strip()))
        resultado_filtrado = resultado_mostrar[resultado_mostrar['Título'].str.contains(regex, case=False, na=False, regex=True)]
    else:
        resultado_filtrado = resultado_mostrar
    st.dataframe(resultado_filtrado.head(30), use_container_width=True)

    # --- DESCARGA DE RESULTADOS COMPLETOS ---
    csv = resultado_mostrar.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descargar todos los resultados como CSV",
        data=csv,
        file_name='reporte_completo.csv',
        mime='text/csv'
    )

    # --- VISUALIZACIONES ---
    st.subheader("Visualizaciones automáticas")

    # 1. Filtrar títulos realmente periodísticos (sin filas de resumen)
    resultado_graficos = resultado_mostrar[
        (resultado_mostrar['Título'].str.lower() != 'total') &
        (resultado_mostrar['Título'].notnull()) &
        (resultado_mostrar['Título'].str.len() > 20)  # Opcional, podés ajustar
    ]
    
    # 2. Lecturas promedio según extensión del título
    st.markdown("#### Lecturas promedio según extensión del título")
    if not resultado_graficos.empty:
        promedios_ext = resultado_graficos.groupby('Extensión')['Total de pageviews'].mean().reset_index()
        fig1, ax1 = plt.subplots()
        ax1.plot(promedios_ext['Extensión'], promedios_ext['Total de pageviews'])
        ax1.set_xlabel('Extensión del título (caracteres)')
        ax1.set_ylabel('Lecturas promedio')
        ax1.set_title('Lecturas promedio según longitud del título')
        st.pyplot(fig1)
    else:
        st.warning("No hay suficientes datos para graficar lecturas por extensión.")

    # --- ANALISIS DE LECTURAS SEGÚN EXTENSIÓN DEL TÍTULO EN DISCOVER ---
    st.markdown("#### Lecturas promedio según extensión del título en Google Discover")
    discover = resultado_mostrar[resultado_mostrar['Fuente principal'].str.lower() == "google discover"]
    
    if not discover.empty:
        promedios_discover = discover.groupby('Extensión')['Total de pageviews'].mean()
        fig_disc, ax_disc = plt.subplots(figsize=(7,5))
        ax_disc.plot(promedios_discover.index, promedios_discover.values, color='orange')
        ax_disc.set_title('Lecturas promedio según longitud del título en Discover')
        ax_disc.set_xlabel('Extensión del título (caracteres)')
        ax_disc.set_ylabel('Lecturas promedio')
        st.pyplot(fig_disc)
    else:
        st.info("No hay notas con Google Discover como fuente principal en el dataset cargado.")

    # 3. Lecturas promedio según fuente principal
    st.markdown("#### Lecturas promedio según fuente principal de tráfico")
    if not resultado_graficos.empty:
        fuentes = resultado_graficos.groupby('Fuente principal')['Total de pageviews'].mean().reset_index()
        fig2 = px.bar(fuentes, x='Fuente principal', y='Total de pageviews',
                      title="Lecturas promedio por fuente principal")
        st.plotly_chart(fig2, use_container_width=True)
    
    # 4. Distribución de tonos
    st.markdown("#### Distribución de tonos en los títulos")
    if not resultado_graficos.empty:
        tonos = resultado_graficos['Tono'].value_counts().reset_index()
        tonos.columns = ['Tono', 'Cantidad']
        fig3 = px.pie(tonos, names='Tono', values='Cantidad', title="Distribución de tonos en títulos")
        st.plotly_chart(fig3, use_container_width=True)
    
    # 5. Proporción de títulos con/sin entidades
    st.markdown("#### Proporción de títulos con y sin entidades")
    if not resultado_graficos.empty:
        entidades = resultado_graficos['¿Tiene entidades?'].value_counts().reset_index()
        entidades.columns = ['¿Tiene entidades?', 'Cantidad']
        fig4 = px.pie(entidades, names='¿Tiene entidades?', values='Cantidad', title="Títulos con/sin entidades")
        st.plotly_chart(fig4, use_container_width=True)
    
    # 6. Lecturas promedio por tono
    st.markdown("#### Lecturas promedio según tono de título")
    if not resultado_graficos.empty:
        tonos2 = resultado_graficos.groupby('Tono')['Total de pageviews'].mean().reset_index()
        fig5 = px.bar(tonos2, x='Tono', y='Total de pageviews', title="Lecturas promedio por tono de título")
        st.plotly_chart(fig5, use_container_width=True)

else:
    st.info("Esperando que subas ambos archivos CSV para mostrar los resultados.")

