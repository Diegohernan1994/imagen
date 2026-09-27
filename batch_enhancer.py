import os
import subprocess
import cv2
import requests
import time
import base64
from pathlib import Path
from enhancer import enhance_hdr_and_sharpness, correct_perspective

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

def process_with_magnific_api(image_path, api_key, prompt):
    """
    Sube la imagen a la API de Magnific.
    """
    with open(image_path, "rb") as f:
        img_bytes = f.read()
        
    encoded = base64.b64encode(img_bytes).decode('utf-8')
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    submit_url = "https://api.magnific.ai/v1/upscale"
    
    payload = {
        "image": encoded,
        "prompt": prompt,
        "creativity": 3,
        "hdr": 3,
        "scale_factor": 2
    }
    
    try:
        res = requests.post(submit_url, json=payload, headers=headers, timeout=30)
        res.raise_for_status()
        data = res.json()
        job_id = data.get("job_id")
        if not job_id:
            return None
            
        status_url = f"https://api.magnific.ai/v1/jobs/{job_id}"
        for _ in range(60): # Esperar max 1 minuto
            time.sleep(2)
            st_res = requests.get(status_url, headers=headers)
            st_data = st_res.json()
            if st_data.get("status") == "completed":
                result_url = st_data.get("result_url")
                if result_url:
                    final_res = requests.get(result_url)
                    return final_res.content
                return None
            elif st_data.get("status") == "failed":
                return None
        return None
    except Exception as e:
        print(f"Magnific API Error: {e}")
        return None

def enhance_single_image(input_path, output_path, mode="magnific", preset="General", api_key=None, auto_perspective=True):
    input_path = Path(input_path)
    output_path = Path(output_path).with_suffix(".jpg")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    img = cv2.imread(str(input_path))
    if img is None:
        return False, "No se pudo leer la imagen"
        
    if auto_perspective:
        img = correct_perspective(img)
        
    img_hdr = enhance_hdr_and_sharpness(img, preset=preset, scale=1)
    jpg_params = [int(cv2.IMWRITE_JPEG_QUALITY), 100]
    
    if mode == "rapido" or not api_key:
        cv2.imwrite(str(output_path), img_hdr, jpg_params)
        return True, "HDR y Perspectiva local completado"
        
    temp_up = str(output_path.parent / f"_temp_{output_path.stem}.jpg")
    cv2.imwrite(temp_up, img_hdr, jpg_params)
    
    magnific_prompt = "professional real estate interior photography, perfect lighting, ultra detailed, clear exterior view outside window, 4k resolution, architectural digest"
    if preset == "Kitchen":
        magnific_prompt = "professional kitchen remodeling photography, modern design, perfect lighting, exterior view through window, 4k"
    elif preset == "Pool":
        magnific_prompt = "luxury backyard pool and spa, hardscaping, perfect blue water, sunny day, professional real estate photography"
        
    magnific_result_bytes = process_with_magnific_api(temp_up, api_key, magnific_prompt)
    
    if os.path.exists(temp_up):
        os.remove(temp_up)
        
    if magnific_result_bytes:
        with open(output_path, "wb") as f:
            f.write(magnific_result_bytes)
        return True, "Procesado con Magnific AI (Window Pull + Upscale)"
    else:
        cv2.imwrite(str(output_path), img_hdr, jpg_params)
        return True, "Procesado localmente (Fallo al contactar API Magnific)"
