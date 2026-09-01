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

# 2. Mostrar mensaje de éxito si viene de un guardado exitoso anterior
if "exito" in st.session_state:
    st.success(st.session_state["exito"])
    del st.session_state["exito"] # Lo borramos para que no se quede pegado

st.title("Bitácora de Primeros Auxilios 🚑")

# 3. Listas de valores
CARGOS = ["Operario de producción", "Ayudante", "Maestro", "Encargado de turno", "Jefe producción", "Jefe de planta", "Jefe operaciones", "Auxiliar de aseo", "Monitor de calidad", "Jefe calidad", "Lavado de bandejas", "Administrativo", "Bodeguero"]
AREAS = ["Bodega", "Masas", "Corte", "Horno", "Envasado", "Calidad", "Operaciones", "Mantención", "Administrativo"]
PLANTAS = ["La Florida", "Quilicura"]
LESIONES = ["Herida cortante", "Herida abrasiva", "Quemadura", "Contusión", "Muscular", "Desgarro", "Otro"]
PARTES_CUERPO = ["Manos", "Dedos", "Brazo", "Cabeza", "Ojos", "Pierna", "Pie"]
INSUMOS_DISPONIBLES = ["Gasa 5x5 cm", "Gasa 7,5x7,5", "Apósito", "Venda gasa elasticada", "Tela adhesiva papel", "Tela adhesiva transpore", "Sutura cutánea", "Compresa fría", "Gasa parafinada", "Toallita de alcohol"]

# 4. Interfaz de Registro (Sin st.form para permitir campos dinámicos)
st.subheader("Datos del Afectado y Accidente")

col1, col2 = st.columns(2)
with col1:
    nombre = st.text_input("Nombre y Apellido Afectado*", key="nombre")
    cargo = st.selectbox("Cargo", CARGOS, index=None, placeholder="Seleccione...", key="cargo")
    area = st.selectbox("Área", AREAS, index=None, placeholder="Seleccione...", key="area")
    encargado = st.text_input("Nombre y Apellido Encargado de Turno", key="encargado")

with col2:
    planta = st.selectbox("Planta", PLANTAS, index=None, placeholder="Seleccione...", key="planta")
    
    zona_chile = ZoneInfo("America/Santiago")
    ahora = datetime.datetime.now(zona_chile)
    
    fecha = st.date_input("Fecha", ahora.date(), key="fecha")
    hora = st.time_input("Hora", ahora.time(), key="hora")
    
    # Campo interactivo de Lesión
    tipo_lesion = st.selectbox("Tipo de Lesión*", LESIONES, index=None, placeholder="Seleccione...", key="tipo_lesion")
    
    lesion_final = tipo_lesion
    if tipo_lesion == "Otro":
        lesion_final = st.text_input("Especifique el tipo de lesión*", key="lesion_otro")
        
    parte_cuerpo = st.selectbox("Parte del Cuerpo Lesionada*", PARTES_CUERPO, index=None, placeholder="Seleccione...", key="parte_cuerpo")
    derivacion_achs = st.selectbox("¿Derivación ACHS?*", ["No", "Sí"], index=None, placeholder="Seleccione...", key="derivacion_achs")

st.divider()
st.subheader("Insumos Utilizados")

insumos_seleccionados = st.multiselect("Seleccione los insumos (puede elegir varios)", INSUMOS_DISPONIBLES, placeholder="Haga clic para seleccionar...", key="insumos")

# Botón de guardado (primary lo pinta de color para que destaque)
submit_button = st.button("Registrar Accidente", type="primary")

# 5. Lógica de inserción en Base de Datos y limpieza manual
if submit_button:
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
            "hora": str(hora.strftime("%H:%M:%S")),
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
                
                # Limpiamos todos los campos reseteando la memoria
                campos_a_limpiar = ["nombre", "cargo", "area", "encargado", "planta", "tipo_lesion", "lesion_otro", "parte_cuerpo", "derivacion_achs", "insumos"]
                for key in campos_a_limpiar:
                    if key in st.session_state:
                        del st.session_state[key]
                
                # Guardamos el mensaje de éxito y recargamos la app entera
                st.session_state["exito"] = f"✅ Registro de {nombre} guardado correctamente. El formulario está listo para un nuevo ingreso."
                st.rerun()
                
            else:
                st.error("No se pudo obtener la respuesta de la base de datos.")
                
        except Exception as e:
            st.error(f"Error al guardar en Supabase: {str(e)}")
