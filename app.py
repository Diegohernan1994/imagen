import streamlit as st
import os
import io
import zipfile
import tempfile
from pathlib import Path
from batch_enhancer import enhance_single_image

st.set_page_config(page_title="California Remodeling Photo Enhancer", layout="wide")

st.markdown("""
<style>
    div[data-testid="stImage"] > img {
        max-height: 320px;
        width: auto;
        object-fit: contain;
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    div[data-testid="stImage"]:fullscreen > img,
    div[data-testid="stImage"]:-webkit-full-screen > img {
        max-height: 95vh !important;
        width: auto !important;
        max-width: 95vw !important;
        object-fit: contain !important;
        margin: auto !important;
        display: block !important;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Configuracion Nube")
    st.info("Para lograr calidad 'Revista' (Window Pulls y alta definicion), ingresa tu API Key de Magnific.")
    env_key = os.getenv("MAGNIFIC_API_KEY", ""); api_key = st.text_input("Magnific API Key", type="password", value=env_key)
    
    st.markdown("---")
    auto_perspective = st.toggle("Enderezar Paredes Automaticamente", value=True)
    st.caption("Endereza la foto localmente antes de enviarla a la API.")

st.title("California Remodeling — Auto Photo Enhancer Pro (Cloud)")
st.markdown("Arrastra tus fotos de proyectos, procesalas masivamente con **Magnific AI** y descargalas en **JPG de Maxima Calidad**.")

tab1, tab2 = st.tabs(["Subida Masiva y Comparativa", "Prueba Rapida Individual"])

with tab1:
    st.subheader("Subida Masiva con Magnific AI")
    
    uploaded_files = st.file_uploader(
        "Arrastra y suelta todas tus fotos aqui",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True
    )
    
    col1, col2 = st.columns(2)
    with col1:
        preset_choice = st.selectbox(
            "Categoria / Preset", 
            ["Auto-detectar", "General", "Kitchen", "Bathroom", "Pool", "Roofing", "Pavers"]
        )
    with col2:
        mode_choice = st.radio(
            "Motor de Procesamiento",
            [
                "Magnific Relight (Reconstruye iluminación quemada y paisaje exterior)",
                "Magnific Upscaler Sparkle (Solo Super-Resolución y Nitidez)",
                "Modo Local Rapido (Dehaze + Contraste, sin API)"
            ],
            index=0
        )
        
    if "Relight" in mode_choice:
        selected_mode = "magnific_relight"
    elif "Magnific" in mode_choice or "Upscaler" in mode_choice:
        selected_mode = "magnific"
    else:
        selected_mode = "rapido"
    
    if uploaded_files:
        st.info(f"Se cargaron {len(uploaded_files)} fotos listas para procesar.")
        
        if st.button("Procesar Todas y Ver Comparativas", type="primary", use_container_width=True):
            if selected_mode != "rapido" and not api_key:
                st.error("Por favor, ingresa tu Magnific API Key en el panel lateral para usar los motores de Magnific AI.")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                results_to_display = []
                zip_buffer = io.BytesIO()
                
                with tempfile.TemporaryDirectory() as temp_work_dir:
                    in_dir = Path(temp_work_dir) / "input"
                    out_dir = Path(temp_work_dir) / "output"
                    in_dir.mkdir()
                    out_dir.mkdir()
                    
                    total = len(uploaded_files)
                    for i, file_obj in enumerate(uploaded_files):
                        file_path = in_dir / file_obj.name
                        with open(file_path, "wb") as f:
                            f.write(file_obj.getbuffer())
                            
                        p = preset_choice
                        if p == "Auto-detectar":
                            name_lower = file_obj.name.lower()
                            if any(k in name_lower for k in ["kitchen", "cocina"]):
                                p = "Kitchen"
                            elif any(k in name_lower for k in ["bath", "baño"]):
                                p = "Bathroom"
                            elif any(k in name_lower for k in ["pool", "piscina", "spa"]):
                                p = "Pool"
                            elif any(k in name_lower for k in ["roof", "techo"]):
                                p = "Roofing"
                            elif any(k in name_lower for k in ["paver", "patio"]):
                                p = "Pavers"
                            else:
                                p = "General"
                                
                        out_path = out_dir / file_obj.name
                        status_text.markdown(f"**Procesando [{i+1}/{total}]:** `{file_obj.name}`...")
                        
                        ok, msg = enhance_single_image(file_path, out_path, mode=selected_mode, preset=p, api_key=api_key, auto_perspective=auto_perspective)
                        
                        target_out = out_path.with_suffix(".jpg")
                        if ok and target_out.exists():
                            with open(target_out, "rb") as of:
                                out_bytes = of.read()
                            results_to_display.append({
                                "name": file_obj.name,
                                "preset": p,
                                "original": file_obj.getvalue(),
                                "enhanced": out_bytes
                            })
                        else:
                            st.error(f"Error procesando {file_obj.name}: {msg}")
                            
                        progress_bar.progress((i + 1) / total)
                        
                    status_text.markdown("**Preparando archivo ZIP para descarga...**")
                    
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for item in results_to_display:
                            zip_file.writestr(Path(item["name"]).stem + "_mejorada.jpg", item["enhanced"])
                            
                    zip_buffer.seek(0)
                    
                    st.session_state["batch_results"] = results_to_display
                    st.session_state["zip_data"] = zip_buffer.getvalue()
                    st.success(f"Listo! Se completaron {len(results_to_display)} fotos con exito.")

    if "batch_results" in st.session_state and st.session_state["batch_results"]:
        st.markdown("---")
        st.download_button(
            label="Descargar Todas las Fotos Mejoradas (.ZIP)",
            data=st.session_state["zip_data"],
            file_name="remodeling_fotos_mejoradas.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True
        )
        
        st.subheader("Galeria de Comparativas")
        for item in st.session_state["batch_results"]:
            with st.expander(f"Foto: {item['name']} | Preset: {item['preset']}", expanded=True):
                col_orig, col_res = st.columns(2)
                with col_orig:
                    st.caption("Original")
                    st.image(item["original"], use_container_width=False)
                with col_res:
                    st.caption("Mejorada")
                    st.image(item["enhanced"], use_container_width=False)

with tab2:
    st.subheader("Prueba Rapida Individual")
    single_file = st.file_uploader("Sube una sola foto", type=["jpg", "jpeg", "png", "webp"], key="single_test")
    
    if single_file:
        temp_input = Path("temp_test_input.jpg")
        temp_output = Path("temp_test_output.jpg")
        with open(temp_input, "wb") as f:
            f.write(single_file.getbuffer())
            
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            test_preset = st.selectbox("Categoria / Preset", ["Kitchen", "Bathroom", "Pool", "Roofing", "Pavers", "General"], key="test_cat")
        with col_t2:
            test_mode = st.radio(
                "Motor",
                [
                    "Magnific Relight (Ventanas y Luz)",
                    "Magnific Upscaler (Nitidez)",
                    "Modo Local Rapido"
                ],
                key="test_single_m"
            )
            
        if "Relight" in test_mode:
            selected_m = "magnific_relight"
        elif "Magnific" in test_mode or "Upscaler" in test_mode:
            selected_m = "magnific"
        else:
            selected_m = "rapido"
        
        if st.button("Mejorar Foto de Prueba"):
            if selected_m != "rapido" and not api_key:
                st.error("Falta ingresar Magnific API Key en el panel lateral.")
            else:
                with st.spinner("Procesando..."):
                    ok, msg = enhance_single_image(temp_input, temp_output, mode=selected_m, preset=test_preset, api_key=api_key, auto_perspective=auto_perspective)
                    target_out = temp_output.with_suffix(".jpg")
                    if ok and target_out.exists():
                        st.success(f"Estado: {msg}")
                        col_orig, col_res = st.columns(2)
                        with col_orig:
                            st.caption("Original")
                            st.image(str(temp_input), use_container_width=False)
                        with col_res:
                            st.caption("Mejorada")
                            st.image(str(target_out), use_container_width=False)
                    else:
                        st.error(f"Fallo: {msg}")

