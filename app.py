import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import glob
import os

# Definir las URLs y los fondos correspondientes
urls_fondos = {
    'A': 'https://www.spensiones.cl/apps/valoresCuotaFondo/vcfAFP.php?tf=A',
    'B': 'https://www.spensiones.cl/apps/valoresCuotaFondo/vcfAFP.php?tf=B',
    'C': 'https://www.spensiones.cl/apps/valoresCuotaFondo/vcfAFP.php?tf=C',
    'D': 'https://www.spensiones.cl/apps/valoresCuotaFondo/vcfAFP.php?tf=D',
    'E': 'https://www.spensiones.cl/apps/valoresCuotaFondo/vcfAFP.php?tf=E'
}

# Cuotas ingresadas manualmente con los nombres correctos de las AFP y fechas
cuotas_manual = {
    ('UNO', 'A'): ('*', '*'),
    ('UNO', 'B'): ('*', '*'),
    ('UNO', 'C'): ('*', '*'),
    ('UNO', 'D'): ('*', '*'),
    ('UNO', 'E'): ('*', '*'),
    ('CAPITAL', 'A'): ('*', '*'),
    ('CAPITAL', 'B'): ('*', '*'),
    ('CAPITAL', 'C'): ('*', '*'),
    ('CAPITAL', 'D'): ('*', '*'),
    ('CAPITAL', 'E'): ('*', '*'),
    ('CUPRUM', 'A'): ('*', '*'),
    ('CUPRUM', 'B'): ('*', '*'),
    ('CUPRUM', 'C'): ('*', '*'),
    ('CUPRUM', 'D'): ('*', '*'),
    ('CUPRUM', 'E'): ('*', '*'),
    ('HABITAT', 'A'): ('*', '*'),
    ('HABITAT', 'B'): ('*', '*'),
    ('HABITAT', 'C'): ('*', '*'),
    ('HABITAT', 'D'): ('*', '*'),
    ('HABITAT', 'E'): ('*', '*'),
    ('MODELO', 'A'): ('66914.78', '2023-06-10),
    ('MODELO', 'B'): ('56588.56', '2023-06-10),
    ('MODELO', 'C'): ('61091.02', '2023-06-10),
    ('MODELO', 'D'): ('45719.21', '2023-06-10),
    ('MODELO', 'E'): ('57054.59', '2023-06-10),
    ('PLANVITAL', 'A'): ('*', '*'),
    ('PLANVITAL', 'B'): ('*', '*'),
    ('PLANVITAL', 'C'): ('*', '*'),
    ('PLANVITAL', 'D'): ('*', '*'),
    ('PLANVITAL', 'E'): ('*', '*'),
    ('PROVIDA', 'A'): ('68244,05', '2023-06-10),
    ('PROVIDA', 'B'): ('57097,72', '2023-06-10'),
    ('PROVIDA', 'C'): ('54734,32', '2023-06-10'),
    ('PROVIDA', 'D'): ('44261,24', '2023-06-10'),
    ('PROVIDA', 'E'): ('52669,91', '2023-06-10'),
}

def obtener_datos():
    # Inicializar lista para almacenar los datos de todos los fondos
    dataframes = []
    afp_estado = {afp: {fondo: 'NOT YET' for fondo in urls_fondos.keys()} for afp in set([k[0] for k in cuotas_manual.keys()])}
    fechas_fondos = {}

    # Variable para almacenar la última fecha disponible del web scraping
    ultima_fecha = None

    # Iterar sobre cada URL y fondo
    for fondo, url in urls_fondos.items():
        try:
            # Realizar la solicitud GET
            response = requests.get(url, timeout=10)

            # Verificar si la solicitud fue exitosa
            if response.status_code == 200:
                # Parsear el contenido HTML con BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')

                # Encontrar la fecha
                date_tag = soup.find_all('table', class_='table table-striped table-hover table-bordered table-condensed')[1]
                if date_tag:
                    date_str = date_tag.find_all('center')[0].text.strip().split()[0]
                    if ultima_fecha is None or date_str > ultima_fecha:
                        ultima_fecha = date_str
                    fechas_fondos[fondo] = date_str
                else:
                    date_str = "Fecha no encontrada"

                # Encontrar la tabla correcta
                table = soup.find_all('table', class_='table table-striped table-hover table-bordered table-condensed')[1]

                # Inicializar listas para almacenar los datos
                afp = []
                valor_cuota = []
                valor_patrimonio = []

                # Recorrer las filas de la tabla
                rows = table.find_all('tr')[2:]  # Ajuste para incluir todas las filas relevantes

                for row in rows:
                    columns = row.find_all('td')
                    if len(columns) == 3:  # Asegurarse de que la fila tiene 3 columnas
                        afp.append(columns[0].text.strip())
                        valor_cuota.append(columns[1].text.strip())
                        valor_patrimonio.append(columns[2].text.strip())

                # Crear un DataFrame con los datos
                df = pd.DataFrame({
                    'A.F.P.': afp,
                    'Valor Cuota': valor_cuota,
                    'Valor del Patrimonio': valor_patrimonio,
                    'Fecha': [date_str] * len(afp),
                    'Fondo': [fondo] * len(afp)
                })

                # Agregar el DataFrame a la lista
                dataframes.append(df)

                # Actualizar el estado de las AFP
                for a, v in zip(afp, valor_cuota):
                    estado = "OK" if "*" not in v else "NOT YET"
                    afp_estado[a][fondo] = estado

            else:
                st.error(f"Error al acceder a la página: {response.status_code}")

        except requests.exceptions.RequestException as e:
            st.error(f"Error de conexión: {e}")

    # Incorporar valores de cuota manualmente al DataFrame
    afp_manual = []
    valor_cuota_manual = []
    valor_patrimonio_manual = []
    fecha_manual = []
    fondo_manual = []

    for (afp, fondo), (cuota, fecha) in cuotas_manual.items():
        afp_manual.append(afp)
        valor_cuota_manual.append(cuota)
        valor_patrimonio_manual.append("")
        fecha_manual.append(fecha)
        fondo_manual.append(fondo)

    # Crear DataFrame con los datos ingresados manualmente
    df_manual = pd.DataFrame({
        'A.F.P.': afp_manual,
        'Valor Cuota': valor_cuota_manual,
        'Valor del Patrimonio': valor_patrimonio_manual,
        'Fecha': fecha_manual,
        'Fondo': fondo_manual
    })

    # Agregar el DataFrame manual a la lista
    dataframes.insert(0, df_manual)

    # Concatenar todos los DataFrames en uno solo
    df_consolidado = pd.concat(dataframes, ignore_index=True)

    # Obtener la fecha más reciente considerando tanto el web scraping como los datos manuales
    if ultima_fecha is None:
        # Si no hay fechas de web scraping, tomar la fecha más reciente de los datos manuales
        ultima_fecha = max(fecha for _, (cuota, fecha) in cuotas_manual.items() if fecha != '*')
    elif any(fecha != '*' for _, (cuota, fecha) in cuotas_manual.items()):
        # Si hay fechas manuales, considerar la más reciente entre web scraping y manuales
        ultima_fecha = max(ultima_fecha, max(fecha for _, (cuota, fecha) in cuotas_manual.items() if fecha != '*'))

    # Filtrar el DataFrame consolidado por la última fecha
    df_consolidado = df_consolidado[df_consolidado['Fecha'] == ultima_fecha]

    # Guardar el DataFrame en un archivo CSV
    fecha_archivo = ultima_fecha.replace("/", "-")
    nombre_archivo = f"datos_fondos_{fecha_archivo}.csv"
    df_consolidado.to_csv(nombre_archivo, index=False)

    return df_consolidado, nombre_archivo, afp_estado, ultima_fecha

def limpiar_valores(df):
    df['Valor Cuota'] = df['Valor Cuota'].apply(lambda x: pd.to_numeric(x.replace('.', '').replace(',', '.'), errors='coerce'))
    return df

def obtener_fecha_archivo(nombre_archivo):
    return os.path.splitext(nombre_archivo)[0].split('_')[-1]

# Interfaz de Streamlit
st.title("Rentabilidad Relativa AFP ✌️")

if st.button('Ejecutar Proceso'):
    df_consolidado, nombre_archivo, afp_estado, ultima_fecha = obtener_datos()

    if df_consolidado is not None:
        # Leer y ordenar los archivos CSV disponibles
        archivos_csv = glob.glob('datos_fondos_*.csv')
        archivos_csv.sort(key=obtener_fecha_archivo)

        # Leer el archivo más reciente (actual)
        df_actual = pd.read_csv(archivos_csv[-1])

        # Leer el archivo anterior al más reciente (ayer)
        if len(archivos_csv) > 1:
            df_anterior = pd.read_csv(archivos_csv[-2])
        else:
            df_anterior = pd.DataFrame(columns=df_actual.columns)

        # Limpiar los valores de ambos DataFrames
        df_actual = limpiar_valores(df_actual)
        df_anterior = limpiar_valores(df_anterior)

        # Verificar si ambos DataFrames contienen datos
        if not df_actual.empty and not df_anterior.empty:
            # Fusionar los DataFrames en base a la AFP y Fondo
            df_comparacion = pd.merge(df_actual, df_anterior, on=['A.F.P.', 'Fondo'], suffixes=('_hoy', '_ayer'))

            # Filtrar filas donde 'Valor Cuota' de ambos días sean números (no NaN)
            df_comparacion = df_comparacion.dropna(subset=['Valor Cuota_hoy', 'Valor Cuota_ayer'])

            # Calcular la rentabilidad
            df_comparacion['Rentabilidad'] = (df_comparacion['Valor Cuota_hoy'] - df_comparacion['Valor Cuota_ayer']) / df_comparacion['Valor Cuota_ayer'] * 100

            # Seleccionar las columnas para la tabla final
            df_resultado = df_comparacion[['A.F.P.', 'Fondo', 'Valor Cuota_hoy', 'Valor Cuota_ayer', 'Rentabilidad', 'Fecha_hoy']]

            # Filtrar los datos de AFP Provida
            provida_data = df_comparacion[df_comparacion['A.F.P.'] == 'PROVIDA']

            # Verificar si hay datos de rentabilidad para AFP Provida
            if not provida_data.empty:
                # Crear una tabla para almacenar las diferencias de rentabilidad
                fondos = df_comparacion['Fondo'].unique()
                afps = df_comparacion['A.F.P.'].unique()
                afps = afps[afps != 'PROVIDA']  # Excluir AFP Provida

                # Inicializar la tabla con NaN
                rentabilidad_diferencia = pd.DataFrame(index=afps, columns=fondos, data=pd.NA)

                # Calcular la diferencia de rentabilidad con respecto a AFP Provida
                for fondo in fondos:
                    rentabilidad_provida = provida_data[provida_data['Fondo'] == fondo]['Rentabilidad']
                    if not rentabilidad_provida.empty:
                        for afp in afps:
                            rentabilidad_afp = df_comparacion[(df_comparacion['A.F.P.'] == afp) & (df_comparacion['Fondo'] == fondo)]['Rentabilidad']
                            if not rentabilidad_afp.empty:
                                diferencia = (rentabilidad_provida.values[0] - rentabilidad_afp.values[0]) * 100
                                rentabilidad_diferencia.loc[afp, fondo] = round(diferencia, 1)

                # Mostrar la tabla de diferencias de rentabilidad con respecto a Provida
                st.write("Comparación de rentabilidad con respecto a AFP Provida:")
                st.dataframe(rentabilidad_diferencia)
            else:
                st.write("No hay datos de rentabilidad para AFP Provida en este día.")

            # Mostrar la última fecha disponible
            st.write(f"Última fecha disponible en el web scraping: {ultima_fecha}")

            # Convertir el diccionario de estado de AFP a un DataFrame
            afp_estado_df = pd.DataFrame(afp_estado).T
            afp_estado_df.index.name = 'AFP'
            afp_estado_df.columns.name = 'Fondo'
            
            # Mostrar el estado de cada AFP
            st.write("Estado de cada AFP:")
            st.dataframe(afp_estado_df)
        else:
            st.write("No se pudieron obtener datos suficientes para la comparación.")
