import os
import subprocess
import cv2
import requests
import time
import base64
from pathlib import Path
from enhancer import prepare_photographic_base, correct_perspective

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

def process_with_magnific_api(image_path, api_key, prompt, creativity=4, hdr=5, resemblance=1, engine="magnific_sparkle"):
    with open(image_path, "rb") as f:
        img_bytes = f.read()
        
    encoded = base64.b64encode(img_bytes).decode('utf-8')
    
    headers = {
        "x-magnific-api-key": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    submit_url = "https://api.magnific.com/v1/ai/image-upscaler"
    
    payload = {
        "image": encoded,
        "prompt": prompt,
        "creativity": int(round(creativity)),
        "hdr": int(round(hdr)),
        "resemblance": int(round(resemblance)),
        "engine": engine,
        "scale_factor": "2x"
    }
    
    try:
        res = requests.post(submit_url, json=payload, headers=headers, timeout=30)
        if res.status_code != 200:
            return None, f"Error API Magnific: {res.status_code} - {res.text}"
            
        data = res.json()
        inner = data.get("data", {})
        job_id = inner.get("task_id") or data.get("id")
        if not job_id:
            return None, f"No se recibio Job ID. Respuesta completa de Magnific: {data}"
            
        status_url = f"https://api.magnific.com/v1/ai/image-upscaler/{job_id}"
        for _ in range(60): 
            time.sleep(3)
            st_res = requests.get(status_url, headers=headers)
            if st_res.status_code != 200:
                continue
            st_data = st_res.json()
            st_inner = st_data.get("data", {})
            status = st_inner.get("status", "").upper()
            
            if status in ["COMPLETED", "SUCCEEDED", "SUCCESS"]:
                generated = st_inner.get("generated", [])
                if generated and isinstance(generated, list):
                    # Guessing the url key: "url", "image_url", or just the string if it's a list of strings
                    first_gen = generated[0]
                    result_url = first_gen if isinstance(first_gen, str) else (first_gen.get("url") or first_gen.get("image_url"))
                    
                    if result_url:
                        final_res = requests.get(result_url)
                        return final_res.content, "Exito"
                return None, f"Status Completado pero no hay URL. Data: {st_data}"
            elif status in ["FAILED", "ERROR"]:
                return None, f"Status failed en Magnific: {st_data}"
        return None, "Timeout esperando a Magnific"
    except Exception as e:
        return None, f"Excepcion: {str(e)}"

def process_with_magnific_relight(image_path, api_key, prompt):
    with open(image_path, "rb") as f:
        img_bytes = f.read()
        
    encoded = base64.b64encode(img_bytes).decode('utf-8')
    
    headers = {
        "x-magnific-api-key": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    submit_url = "https://api.magnific.com/v1/ai/image-relight"
    
    payload = {
        "image": encoded,
        "prompt": prompt,
        "change_background": True,
        "light_transfer_strength": 80,
        "style": "clean",
        "advanced_settings": {
            "whites": 50,
            "blacks": 60,
            "brightness": 35,
            "contrast": 45,
            "saturation": 50,
            "engine": "real"
        }
    }
    
    try:
        res = requests.post(submit_url, json=payload, headers=headers, timeout=30)
        if res.status_code != 200:
            return None, f"Error API Magnific Relight: {res.status_code} - {res.text}"
            
        data = res.json()
        inner = data.get("data", {})
        job_id = inner.get("task_id") or data.get("id")
        if not job_id:
            return None, f"No se recibio Job ID de Relight. Respuesta: {data}"
            
        status_url = f"https://api.magnific.com/v1/ai/image-relight/{job_id}"
        for _ in range(60): 
            time.sleep(3)
            st_res = requests.get(status_url, headers=headers)
            if st_res.status_code != 200:
                continue
            st_data = st_res.json()
            st_inner = st_data.get("data", {})
            status = st_inner.get("status", "").upper()
            
            if status in ["COMPLETED", "SUCCEEDED", "SUCCESS"]:
                generated = st_inner.get("generated", [])
                if generated and isinstance(generated, list):
                    first_gen = generated[0]
                    result_url = first_gen if isinstance(first_gen, str) else (first_gen.get("url") or first_gen.get("image_url"))
                    
                    if result_url:
                        final_res = requests.get(result_url)
                        return final_res.content, "Exito Relight"
                return None, f"Relight completado sin URL: {st_data}"
            elif status in ["FAILED", "ERROR"]:
                return None, f"Status failed en Relight: {st_data}"
        return None, "Timeout esperando a Magnific Relight"
    except Exception as e:
        return None, f"Excepcion Relight: {str(e)}"

def enhance_single_image(input_path, output_path, mode="magnific", preset="General", api_key=None, auto_perspective=True, custom_prompt=""):
    input_path = Path(input_path)
    output_path = Path(output_path).with_suffix(".jpg")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    img = cv2.imread(str(input_path))
    if img is None:
        return False, "No se pudo leer la imagen"
        
    if auto_perspective:
        img = correct_perspective(img)
        
    # Pre-procesado fotográfico: elimina neblina de celular, restaura negros puros y realza colores naturales
    img_preprocessed = prepare_photographic_base(img, preset=preset)
    jpg_params = [int(cv2.IMWRITE_JPEG_QUALITY), 100]
    
    if mode == "rapido" or not api_key:
        cv2.imwrite(str(output_path), img_preprocessed, jpg_params)
        return True, "Procesado localmente con Dehaze y Corrección Fotográfica"
        
    temp_up = str(output_path.parent / f"_temp_{output_path.stem}.jpg")
    cv2.imwrite(temp_up, img_preprocessed, jpg_params)
    
    # Receta del Diseñador: Illusio con creatividad balanceada y prompt arquitectónico detallado
    if custom_prompt and custom_prompt.strip():
        magnific_prompt = custom_prompt.strip()
    elif preset == "Kitchen":
        magnific_prompt = "Award-winning architectural photography of a luxury modern kitchen, pristine matte white shaker cabinets, rich warm natural oak wood floor, matte black kitchen island, natural lighting, large sliding glass door with a crystal clear view of a sunny California backyard, lush green lawn, patio furniture with umbrella, green trees and bright blue sky, architectural digest, sharp focus, 8k, photorealistic"
    elif preset == "Pool":
        magnific_prompt = "Luxury resort backyard pool and spa, crystal clear turquoise water with clean realistic reflections, natural travertine stone pavers, lush green California landscaping, bright sunny daylight, architectural real estate photograph, 8k"
    elif preset == "Bathroom":
        magnific_prompt = "High-end luxury modern bathroom remodel, pristine marble tiles, sparkling modern chrome fixtures, warm natural ambient lighting, clean grout lines, spa atmosphere, architectural digest, 8k"
    elif preset == "Roofing":
        magnific_prompt = "Pristine residential roofing architecture photography, clean architectural shingles with defined texture, modern house exterior, bright clear blue sky, sharp clean lines, 8k"
    elif preset == "Pavers":
        magnific_prompt = "Luxury outdoor living space, high-end stone pavers patio and driveway, rich textured stonework, lush green foliage and lawn, sunny daylight, architectural digest, 8k"
    else:
        magnific_prompt = "Award-winning architectural interior and exterior photography, high-end California home remodel, perfect natural lighting balance, rich true blacks, natural textures, clean lines, crystal clear window views showing lush green garden and blue sky, architectural digest, 8k"
        
    # Parámetros probados del diseñador:
    # engine: magnific_illusio
    # creativity: 4 (inventa el exterior y afila texturas sin alterar la cocina real)
    # resemblance: 0 (fidelidad arquitectónica)
    # hdr: 3.5
    magnific_result_bytes, error_msg = process_with_magnific_api(
        temp_up, api_key, magnific_prompt, 
        creativity=4, hdr=3, resemblance=0, engine="magnific_illusio"
    )
    
    if os.path.exists(temp_up):
        os.remove(temp_up)
        
    if magnific_result_bytes:
        with open(output_path, "wb") as f:
            f.write(magnific_result_bytes)
        return True, "Procesado con Magnific AI (Receta Diseñador Pro)"
    else:
        return False, f"Fallo al contactar API Magnific. Detalle: {error_msg}"


