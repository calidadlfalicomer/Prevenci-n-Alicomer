import streamlit as st
from supabase import create_client, Client
import datetime

# 1. Conexión a Supabase
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

st.title("Bitácora de Primeros Auxilios 🚑")

# 2. Listas de valores extraídas de tu Excel
CARGOS = ["Operario de producción", "Ayudante", "Maestro", "Encargado de turno", "Jefe producción", "Jefe de planta", "Jefe operaciones", "Auxiliar de aseo", "Monitor de calidad", "Jefe calidad"]
AREAS = ["Bodega", "Masas", "Corte", "Horno", "Envasado", "Calidad", "Operaciones", "Mantención", "Administrativo"]
ENCARGADOS = ["Luis Mejias", "Rox Peñaloza", "Lesdamar Barbosa", "Macarena Garay", "Carlos González", "Franco Pistolese", "Junior Gutiérrez"]
PLANTAS = ["La Florida", "Loginsa"]
LESIONES = ["Herida cortante", "Herida abrasiva", "Quemadura", "Contusión", "Muscular", "Desgarro"]
PARTES_CUERPO = ["Manos", "Dedos", "Brazo", "Cabeza", "Ojos", "Pierna", "Pie"]
INSUMOS_DISPONIBLES = ["Gasa 5x5 cm", "Gasa 7,5x7,5", "Apósito", "Venda gasa elasticada", "Tela adhesiva papel", "Tela adhesiva transpore", "Sutura cutánea", "Compresa fría", "Gasa parafinada", "Toallita de alcohol"]

# 3. Formulario de Registro
with st.form("registro_form", clear_on_submit=True):
    st.subheader("Datos del Afectado y Accidente")
    
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre del Afectado*")
        rut = st.text_input("RUT")
        cargo = st.selectbox("Cargo", CARGOS)
        area = st.selectbox("Área", AREAS)
        encargado = st.selectbox("Encargado de Turno", ENCARGADOS)
    
    with col2:
        planta = st.selectbox("Planta", PLANTAS)
        fecha = st.date_input("Fecha", datetime.date.today())
        hora = st.time_input("Hora", datetime.datetime.now().time())
        tipo_lesion = st.selectbox("Tipo de Lesión", LESIONES)
        parte_cuerpo = st.selectbox("Parte del Cuerpo Lesionada", PARTES_CUERPO)
        derivacion_achs = st.radio("¿Derivación ACHS?", ["No", "Sí"])

    st.divider()
    st.subheader("Insumos Utilizados")
    
    # Multiselect reemplaza las 5 columnas del Excel y permite agregar de 1 a N insumos
    insumos_seleccionados = st.multiselect("Seleccione los insumos (puede elegir varios)", INSUMOS_DISPONIBLES)
    
    submit_button = st.form_submit_button(label="Registrar Accidente")

# 4. Lógica de inserción en Base de Datos
if submit_button:
    if not nombre.strip():
        st.error("El nombre del afectado es un campo obligatorio.")
    else:
        # Preparar data de la tabla cabecera
        cabecera_data = {
            "nombre": nombre,
            "rut": rut,
            "cargo": cargo,
            "area": area,
            "encargado_turno": encargado,
            "planta": planta,
            "fecha": str(fecha),
            "hora": str(hora),
            "tipo_lesion": tipo_lesion,
            "parte_cuerpo": parte_cuerpo,
            "derivacion_achs": True if derivacion_achs == "Sí" else False
        }
        
        try:
            # Insertar en botiquin_cabecera
            response_cab = supabase.table("botiquin_cabecera").insert(cabecera_data).execute()
            
            # Validar que se creó correctamente y rescatar el ID generado
            if response_cab.data:
                nuevo_id = response_cab.data[0]['id']
                
                # Insertar en botiquin_detalle si se seleccionaron insumos
                if insumos_seleccionados:
                    detalles_data = [
                        {"cabecera_id": nuevo_id, "insumo": item, "cantidad": 1} 
                        for item in insumos_seleccionados
                    ]
                    supabase.table("botiquin_detalle").insert(detalles_data).execute()
                    
                st.success(f"✅ Registro de {nombre} guardado correctamente (ID: {nuevo_id}).")
            else:
                st.error("No se pudo obtener la respuesta de la base de datos.")
                
        except Exception as e:
            st.error(f"Error al guardar en Supabase: {str(e)}")
