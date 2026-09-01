import streamlit as st
from supabase import create_client, Client
import datetime
from zoneinfo import ZoneInfo

# 1. Conexión a Supabase
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

st.title("Bitácora de Primeros Auxilios 🚑")

# 2. Listas de valores (Actualizadas con nuevos cargos y "Otro" en lesiones)
CARGOS = ["Operario de producción", "Ayudante", "Maestro", "Encargado de turno", "Jefe producción", "Jefe de planta", "Jefe operaciones", "Auxiliar de aseo", "Monitor de calidad", "Jefe calidad", "Lavado de bandejas", "Administrativo", "Bodeguero"]
AREAS = ["Bodega", "Masas", "Corte", "Horno", "Envasado", "Calidad", "Operaciones", "Mantención", "Administrativo"]
PLANTAS = ["La Florida", "Quilicura"]
LESIONES = ["Herida cortante", "Herida abrasiva", "Quemadura", "Contusión", "Muscular", "Desgarro", "Otro"]
PARTES_CUERPO = ["Manos", "Dedos", "Brazo", "Cabeza", "Ojos", "Pierna", "Pie"]
INSUMOS_DISPONIBLES = ["Gasa 5x5 cm", "Gasa 7,5x7,5", "Apósito", "Venda gasa elasticada", "Tela adhesiva papel", "Tela adhesiva transpore", "Sutura cutánea", "Compresa fría", "Gasa parafinada", "Toallita de alcohol"]

# 3. Formulario de Registro
with st.form("registro_form", clear_on_submit=True):
    st.subheader("Datos del Afectado y Accidente")
    
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre y Apellido Afectado*")
        cargo = st.selectbox("Cargo", CARGOS, index=None, placeholder="Seleccione...")
        area = st.selectbox("Área", AREAS, index=None, placeholder="Seleccione...")
        encargado = st.text_input("Nombre y Apellido Encargado de Turno")
    
    with col2:
        planta = st.selectbox("Planta", PLANTAS, index=None, placeholder="Seleccione...")
        
        # Ajuste para que la hora por defecto sea siempre la local de Chile
        zona_chile = ZoneInfo("America/Santiago")
        ahora = datetime.datetime.now(zona_chile)
        
        fecha = st.date_input("Fecha", ahora.date())
        hora = st.time_input("Hora", ahora.time())
        
        # Selección de Lesión con opción "Otro"
        tipo_lesion = st.selectbox("Tipo de Lesión*", LESIONES, index=None, placeholder="Seleccione...")
        
        lesion_final = tipo_lesion
        if tipo_lesion == "Otro":
            lesion_final = st.text_input("Especifique el tipo de lesión*")
            
        parte_cuerpo = st.selectbox("Parte del Cuerpo Lesionada*", PARTES_CUERPO, index=None, placeholder="Seleccione...")
        derivacion_achs = st.selectbox("¿Derivación ACHS?*", ["No", "Sí"], index=None, placeholder="Seleccione...")

    st.divider()
    st.subheader("Insumos Utilizados")
    
    insumos_seleccionados = st.multiselect("Seleccione los insumos (puede elegir varios)", INSUMOS_DISPONIBLES, placeholder="Haga clic para seleccionar...")
    
    # Botón de guardado
    submit_button = st.form_submit_button(label="Registrar Accidente")

# 4. Lógica de inserción en Base de Datos y validaciones
if submit_button:
    # Validación reforzada para incluir el campo de texto cuando se elige "Otro"
    if not nombre.strip() or not lesion_final or (tipo_lesion == "Otro" and not lesion_final.strip()) or not parte_cuerpo or not derivacion_achs:
        st.warning("⚠️ Por favor, complete todos los campos obligatorios (*) antes de guardar.")
    else:
        cabecera_data = {
            "nombre": nombre,
            "cargo": cargo,
            "area": area,
            "encargado_turno": encargado,
            "planta": planta,
            "fecha": str(fecha),
            "hora": str(hora.strftime("%H:%M:%S")), # Formateado seguro para base de datos
            "tipo_lesion": lesion_final,
            "parte_cuerpo": parte_cuerpo,
            "derivacion_achs": True if derivacion_achs == "Sí" else False
        }
        
        try:
            response_cab = supabase.table("botiquin_cabecera").insert(cabecera_data).execute()
            
            if response_cab.data:
                nuevo_id = response_cab.data[0]['id']
                
                if insumos_seleccionados:
                    detalles_data = [
                        {"cabecera_id": nuevo_id, "insumo": item, "cantidad": 1} 
                        for item in insumos_seleccionados
                    ]
                    supabase.table("botiquin_detalle").insert(detalles_data).execute()
                    
                st.success(f"✅ Registro de {nombre} guardado correctamente. El formulario está listo para un nuevo ingreso.")
            else:
                st.error("No se pudo obtener la respuesta de la base de datos.")
                
        except Exception as e:
            st.error(f"Error al guardar en Supabase: {str(e)}")
