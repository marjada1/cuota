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

# Cuotas ingresadas manualmente con los nombres correctos de las AFP
cuotas_manual = {
    ('UNO', 'A'): '*',
    ('UNO', 'B'): '*',
    ('UNO', 'C'): '*',
    ('UNO', 'D'): '*',
    ('UNO', 'E'): '*',
    ('CAPITAL', 'A'): '*',
    ('CAPITAL', 'B'): '*',
    ('CAPITAL', 'C'): '*',
    ('CAPITAL', 'D'): '*',
    ('CAPITAL', 'E'): '*',
    ('CUPRUM', 'A'): '*',
    ('CUPRUM', 'B'): '*',
    ('CUPRUM', 'C'): '*',
    ('CUPRUM', 'D'): '*',
    ('CUPRUM', 'E'): '*',
    ('HABITAT', 'A'): '*',
    ('HABITAT', 'B'): '*',
    ('HABITAT', 'C'): '*',
    ('HABITAT', 'D'): '*',
    ('HABITAT', 'E'): '*',
    ('MODELO', 'A'): '*',
    ('MODELO', 'B'): '*',
    ('MODELO', 'C'): '*',
    ('MODELO', 'D'): '*',
    ('MODELO', 'E'): '*',
    ('PLANVITAL', 'A'): '*',
    ('PLANVITAL', 'B'): '*',
    ('PLANVITAL', 'C'): '*',
    ('PLANVITAL', 'D'): '*',
    ('PLANVITAL', 'E'): '*',
    ('PROVIDA', 'A'): '*',
    ('PROVIDA', 'B'): '*',
    ('PROVIDA', 'C'): '*',
    ('PROVIDA', 'D'): '*',
    ('PROVIDA', 'E'): '*',
}

# Cuotas manuales para la primera cuota del mes y del año
cuotas_mensuales = {
    ('UNO', 'A'): '1000',
    ('UNO', 'B'): '1000',
    ('UNO', 'C'): '1000',
    ('UNO', 'D'): '1000',
    ('UNO', 'E'): '1000',
    ('CAPITAL', 'A'): '1000',
    ('CAPITAL', 'B'): '1000',
    ('CAPITAL', 'C'): '1000',
    ('CAPITAL', 'D'): '1000',
    ('CAPITAL', 'E'): '1000',
    ('CUPRUM', 'A'): '1000',
    ('CUPRUM', 'B'): '1000',
    ('CUPRUM', 'C'): '1000',
    ('CUPRUM', 'D'): '1000',
    ('CUPRUM', 'E'): '1000',
    ('HABITAT', 'A'): '1000',
    ('HABITAT', 'B'): '1000',
    ('HABITAT', 'C'): '1000',
    ('HABITAT', 'D'): '1000',
    ('HABITAT', 'E'): '1000',
    ('MODELO', 'A'): '1000',
    ('MODELO', 'B'): '1000',
    ('MODELO', 'C'): '1000',
    ('MODELO', 'D'): '1000',
    ('MODELO', 'E'): '1000',
    ('PLANVITAL', 'A'): '1000',
    ('PLANVITAL', 'B'): '1000',
    ('PLANVITAL', 'C'): '1000',
    ('PLANVITAL', 'D'): '1000',
    ('PLANVITAL', 'E'): '1000',
    ('PROVIDA', 'A'): '1000',
    ('PROVIDA', 'B'): '1000',
    ('PROVIDA', 'C'): '1000',
    ('PROVIDA', 'D'): '1000',
    ('PROVIDA', 'E'): '1000',
}

cuotas_anuales = {
    ('UNO', 'A'): '900',
    ('UNO', 'B'): '900',
    ('UNO', 'C'): '900',
    ('UNO', 'D'): '900',
    ('UNO', 'E'): '900',
    ('CAPITAL', 'A'): '900',
    ('CAPITAL', 'B'): '900',
    ('CAPITAL', 'C'): '900',
    ('CAPITAL', 'D'): '900',
    ('CAPITAL', 'E'): '900',
    ('CUPRUM', 'A'): '900',
    ('CUPRUM', 'B'): '900',
    ('CUPRUM', 'C'): '900',
    ('CUPRUM', 'D'): '900',
    ('CUPRUM', 'E'): '900',
    ('HABITAT', 'A'): '900',
    ('HABITAT', 'B'): '900',
    ('HABITAT', 'C'): '900',
    ('HABITAT', 'D'): '900',
    ('HABITAT', 'E'): '900',
    ('MODELO', 'A'): '900',
    ('MODELO', 'B'): '900',
    ('MODELO', 'C'): '900',
    ('MODELO', 'D'): '900',
    ('MODELO', 'E'): '900',
    ('PLANVITAL', 'A'): '900',
    ('PLANVITAL', 'B'): '900',
    ('PLANVITAL', 'C'): '900',
    ('PLANVITAL', 'D'): '900',
    ('PLANVITAL', 'E'): '900',
    ('PROVIDA', 'A'): '900',
    ('PROVIDA', 'B'): '900',
    ('PROVIDA', 'C'): '900',
    ('PROVIDA', 'D'): '900',
    ('PROVIDA', 'E'): '900',
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

    # Concatenar todos los DataFrames en uno solo y filtrar por la fecha más reciente
    if dataframes:
        df_consolidado = pd.concat(dataframes, ignore_index=True)
        df_consolidado = df_consolidado[df_consolidado['Fecha'] == ultima_fecha]
    else:
        st.write("No se pudieron obtener datos de ningún fondo.")
        return None, None, None, None

    # Incorporar valores de cuota manualmente al DataFrame
    afp_manual = []
    valor_cuota_manual = []
    valor_patrimonio_manual = []

    for (afp, fondo), cuota in cuotas_manual.items():
        afp_manual.append(afp)
        valor_cuota_manual.append(cuota)
        valor_patrimonio_manual.append("")

    # Crear DataFrame con los datos ingresados manualmente
    if ultima_fecha is not None:
        df_manual = pd.DataFrame({
            'A.F.P.': afp_manual,
            'Valor Cuota': valor_cuota_manual,
            'Valor del Patrimonio': valor_patrimonio_manual,
            'Fecha': [ultima_fecha] * len(afp_manual),
            'Fondo': [fondo for (_, fondo) in cuotas_manual.keys()]
        })
        dataframes.insert(0, df_manual)
    else:
        st.error("No se pudo determinar la última fecha disponible, por lo que no se pueden incluir datos manuales.")
        return None, None, None, None

    # Concatenar todos los DataFrames en uno solo
    df_consolidado = pd.concat(dataframes, ignore_index=True)

    # Reemplazar los valores de cuota (*) con valores manuales si están disponibles
    for index, row in df_consolidado.iterrows():
        if row['Valor Cuota'] == '(*)':
            manual_value = cuotas_manual.get((row['A.F.P.'], row['Fondo']), None)
            if manual_value:
                df_consolidado.at[index, 'Valor Cuota'] = manual_value

    # Priorizar los valores descargados sobre los ingresados manualmente
    df_consolidado.drop_duplicates(subset=['A.F.P.', 'Fondo'], keep='last', inplace=True)

    # Guardar el DataFrame en un archivo CSV
    fecha_archivo = df_consolidado['Fecha'].iloc[0].replace("/", "-")
    nombre_archivo = f"datos_fondos_{fecha_archivo}.csv"
    df_consolidado.to_csv(nombre_archivo, index=False)

    return df_consolidado, nombre_archivo, afp_estado, ultima_fecha

def limpiar_valores(df):
    df['Valor Cuota'] = df['Valor Cuota'].apply(lambda x: pd.to_numeric(x.replace('.', '').replace(',', '.'), errors='coerce'))
    return df

def obtener_fecha_archivo(nombre_archivo):
    return os.path.splitext(nombre_archivo)[0].split('_')[-1]

# Interfaz de Streamlit
st.title("Rentabilidad Relativa AFPs ✌️")

if st.button('Ejecutar Proceso'):
    df_consolidado, nombre_archivo, afp_estado, ultima_fecha = obtener_datos()

    if df_consolidado is not None:
        # Leer y ordenar los archivos CSV disponibles
        archivos_csv = glob.glob('datos_fondos_*.csv')
        archivos_csv.sort(key=obtener_fecha_archivo)

        # Leer el archivo más reciente (actual)
        df_actual = pd.read_csv(archivos_csv[-1])

        # Limpiar los valores del DataFrame actual
        df_actual = limpiar_valores(df_actual)

        # Calcular la rentabilidad MTD y YTD
        rentabilidad_mtd = {}
        rentabilidad_ytd = {}

        for (afp, fondo), cuota_mes in cuotas_mensuales.items():
            cuota_mes = float(cuota_mes.replace(',', '.'))
            cuota_hoy = df_actual[(df_actual['A.F.P.'] == afp) & (df_actual['Fondo'] == fondo)]['Valor Cuota'].values

            if len(cuota_hoy) > 0:
                cuota_hoy = float(cuota_hoy[0])
                rentabilidad_mtd[(afp, fondo)] = ((cuota_hoy - cuota_mes) / cuota_mes) * 100
            else:
                rentabilidad_mtd[(afp, fondo)] = None

        for (afp, fondo), cuota_ano in cuotas_anuales.items():
            cuota_ano = float(cuota_ano.replace(',', '.'))
            cuota_hoy = df_actual[(df_actual['A.F.P.'] == afp) & (df_actual['Fondo'] == fondo)]['Valor Cuota'].values

            if len(cuota_hoy) > 0:
                cuota_hoy = float(cuota_hoy[0])
                rentabilidad_ytd[(afp, fondo)] = ((cuota_hoy - cuota_ano) / cuota_ano) * 100
            else:
                rentabilidad_ytd[(afp, fondo)] = None

        # Filtrar los datos de AFP Provida para MTD y YTD
        rentabilidad_mtd_provida = {k: v for k, v in rentabilidad_mtd.items() if k[0] == 'PROVIDA'}
        rentabilidad_ytd_provida = {k: v for k, v in rentabilidad_ytd.items() if k[0] == 'PROVIDA'}

        # Crear DataFrames para las diferencias MTD y YTD
        mtd_diferencia = pd.DataFrame(index=list(set([k[0] for k in rentabilidad_mtd.keys()]) - {'PROVIDA'}), columns=urls_fondos.keys(), data=pd.NA)
        ytd_diferencia = pd.DataFrame(index=list(set([k[0] for k in rentabilidad_ytd.keys()]) - {'PROVIDA'}), columns=urls_fondos.keys(), data=pd.NA)

        for (afp, fondo) in rentabilidad_mtd:
            if afp != 'PROVIDA' and (afp, fondo) in rentabilidad_mtd_provida:
                mtd_diferencia.loc[afp, fondo] = rentabilidad_mtd_provida[('PROVIDA', fondo)] - rentabilidad_mtd[(afp, fondo)]

        for (afp, fondo) in rentabilidad_ytd:
            if afp != 'PROVIDA' and (afp, fondo) in rentabilidad_ytd_provida:
                ytd_diferencia.loc[afp, fondo] = rentabilidad_ytd_provida[('PROVIDA', fondo)] - rentabilidad_ytd[(afp, fondo)]

        # Mostrar las tablas de diferencias MTD y YTD con respecto a Provida
        st.write("Diferencia de Rentabilidad Acumulada (MTD) con respecto a AFP Provida ✌️:")
        st.dataframe(mtd_diferencia)

        st.write("Diferencia de Rentabilidad Acumulada (YTD) con respecto a AFP Provida ✌️:")
        st.dataframe(ytd_diferencia)

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
