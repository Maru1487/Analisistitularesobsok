import streamlit as st
import pandas as pd
import spacy
import re

# Intenta cargar el modelo; si falla lo instala
try:
    nlp = spacy.load("es_core_news_sm")
except OSError:
    import subprocess
    import sys
    subprocess.run([sys.executable, "-m", "spacy", "download", "es_core_news_sm"])
    nlp = spacy.load("es_core_news_sm")

# --------- LISTA DE ENTIDADES MANUALES URUGUAYAS ---------
entidades_locales_uy = [
    "IRPF", "BPS", "DGI", "AFAP", "ANEP", "CODICEN", "UTE", "OSE", "ANTEL", "MIDES", 
    "MGAP", "MEF", "MEC", "MI", "MSP", "MTOP", "MRREE", "INAU", "INISA", 
    "FA", "PN", "PC", "CA", "TC", "SCJ", "IMM", "BHU", "BROU", "Banco República", 
    "FONASA", "SNIC", "UTU", "Universidad de la República", "Udelar", "ANV", "ANCAP", 
    "INE", "INUMET", "IMPO", "PIT-CNT", "SIIAS", "CNCS", "SMU", "ASSE", "SUINAU", 
    "Sunca", "Conaprole", "COFE", "CUTCSA", "IASS", "MIEM", "MTSS", "FFAA", "FAU", 
    "ANP", "TCR", "INDDHH", "AUF", "COPSA", "TCA", "PJ", "PE", "TOCAF"
]

# --------- LISTA DE VERBOS DECLARATIVOS ---------
verbos_declarativos = [
    "anunció", "anunciará", "confirmó", "confirmará", "decidió", "decidirá", 
    "rechazó", "rechazará", "defendió", "defenderá", "cuestionó", "cuestionará",
    "propuso", "propondrá", "sostuvo", "sostendrá", "denunció", "denunciará", 
    "convocó", "convocará", "presentó", "presentará", "pidió", "pedirá",
    "apoyó", "apoyará", "criticó", "criticarán", "celebró", "celebrará"
]

# --------- FUNCIONES DE ANÁLISIS ---------
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

# --------- STREAMLIT APP ---------
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

    # --- ANALISIS SINTÁCTICO AVANZADO ---
    resultado['longitud_titulo'] = resultado['title'].apply(len)
    resultado['entidades'] = resultado['title'].apply(extraer_entidades)
    resultado['tiene_entidades'] = resultado['entidades'].apply(lambda x: "sí" if len(x) > 0 else "no")
    resultado['cantidad_entidades'] = resultado['entidades'].apply(len)
    resultado['tono_titulo'] = resultado['title'].apply(detectar_tono)
    resultado['tiene_cita'] = resultado['title'].apply(tiene_cita)
    resultado['posicion_entidad'] = resultado.apply(lambda row: posicion_entidad(row['title'], row['entidades']), axis=1)
    resultado['estilo_titulo'] = resultado.apply(lambda row: determinar_estilo(row['title'], row['entidades']), axis=1)
    resultado['formato_numerico'] = resultado['title'].apply(analizar_numeros)
    resultado['tiene_numeros'] = resultado['title'].apply(tiene_numeros)
    resultado['cantidad_numeros'] = resultado['title'].apply(cantidad_numeros)

    # ENCABEZADOS AMIGABLES
    resultado_mostrar = resultado.rename(columns={
        'title': 'Título',
        'pageviewstotal': 'Total de pageviews',
        'fuente_principal': 'Fuente principal',
        'porcentaje_fuente_principal': 'Porcentaje de la fuente principal',
        'longitud_titulo': 'Extensión',
        'entidades': 'Entidades',
        'tiene_entidades': '¿Tiene entidades?',
        'cantidad_entidades': 'Cantidad de entidades',
        'tono_titulo': 'Tono',
        'tiene_cita': '¿Cita?',
        'posicion_entidad': 'Posición entidad',
        'estilo_titulo': 'Estilo',
        'formato_numerico': 'Formato numérico',
        'tiene_numeros': '¿Tiene números?',
        'cantidad_numeros': 'Cantidad de números'
    })

    st.subheader("Tabla principal: todas las variables de análisis sintáctico")
    st.dataframe(resultado_mostrar, use_container_width=True)

    import matplotlib.pyplot as plt

st.subheader("Top 20 notas más leídas (gráfico de barras)")

top20 = resultado_mostrar.head(20)
fig, ax = plt.subplots(figsize=(10, 7))
ax.barh(top20['Título'][::-1], top20['Total de pageviews'][::-1], color='#3683d4')
ax.set_xlabel('Lecturas')
ax.set_ylabel('Título')
ax.set_title('Top 20 notas más leídas')
plt.tight_layout()
st.pyplot(fig)

# --------- FILTRO TEMÁTICO ROBUSTO (palabra exacta o expresión) ---------
st.subheader("Filtrar títulos por palabra clave (palabra exacta)")
palabra_clave = st.text_input(
    "Ingresá una palabra o expresión exacta para filtrar títulos (distingue palabra aislada):", "")

if palabra_clave:
    regex = r'\b{}\b'.format(re.escape(palabra_clave.strip()))
    resultado_filtrado = resultado_mostrar[resultado_mostrar['Título'].str.contains(regex, case=False, na=False, regex=True)]
else:
    resultado_filtrado = resultado_mostrar

st.dataframe(resultado_filtrado, use_container_width=True)

# Botón de descarga SIEMPRE PARA TODOS LOS RESULTADOS
csv = resultado_mostrar.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Descargar todos los resultados como CSV",
    data=csv,
    file_name='reporte_completo.csv',
    mime='text/csv'
)
else:
    st.info("Esperando que subas ambos archivos CSV para mostrar los resultados.")
