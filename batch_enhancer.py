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
    with open(image_path, "rb") as f:
        img_bytes = f.read()
        
    encoded = base64.b64encode(img_bytes).decode('utf-8')
    
    headers = {
        "x-magnific-api-key": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    submit_url = "https://api.magnific.ai/v1/ai/image-upscaler"
    
    payload = {
        "image": encoded,
        "prompt": prompt,
        "creativity": 3,
        "hdr": 3,
        "scale_factor": "2x"
    }
    
    try:
        res = requests.post(submit_url, json=payload, headers=headers, timeout=30)
        if res.status_code != 200:
            return None, f"Error API Magnific: {res.status_code} - {res.text}"
            
        data = res.json()
        job_id = data.get("task_id") or data.get("id") or data.get("job_id")
        if not job_id:
            return None, "No se recibio Job ID de Magnific"
            
        status_url = f"https://api.magnific.ai/v1/ai/image-upscaler/{job_id}" # Guessing status endpoint based on typical REST
        for _ in range(60): 
            time.sleep(3)
            st_res = requests.get(status_url, headers=headers)
            if st_res.status_code != 200:
                continue
            st_data = st_res.json()
            status = st_data.get("status")
            if status == "completed" or status == "succeeded":
                result_url = st_data.get("result_url") or st_data.get("output")
                if result_url:
                    final_res = requests.get(result_url)
                    return final_res.content, "Exito"
                return None, "No result URL"
            elif status == "failed":
                return None, "Status failed en Magnific"
        return None, "Timeout esperando a Magnific"
    except Exception as e:
        return None, f"Excepcion: {str(e)}"

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
        return True, "Procesado localmente (Sin API)"
        
    temp_up = str(output_path.parent / f"_temp_{output_path.stem}.jpg")
    cv2.imwrite(temp_up, img_hdr, jpg_params)
    
    magnific_prompt = "professional real estate interior photography, perfect lighting, ultra detailed, clear exterior view outside window, 4k resolution, architectural digest"
    if preset == "Kitchen":
        magnific_prompt = "professional kitchen remodeling photography, modern design, perfect lighting, exterior view through window, 4k"
    elif preset == "Pool":
        magnific_prompt = "luxury backyard pool and spa, hardscaping, perfect blue water, sunny day, professional real estate photography"
        
    magnific_result_bytes, error_msg = process_with_magnific_api(temp_up, api_key, magnific_prompt)
    
    if os.path.exists(temp_up):
        os.remove(temp_up)
        
    if magnific_result_bytes:
        with open(output_path, "wb") as f:
            f.write(magnific_result_bytes)
        return True, "Procesado con Magnific AI (Window Pull + Upscale)"
    else:
        cv2.imwrite(str(output_path), img_hdr, jpg_params)
        return True, f"Fallo API, se aplico mejora local. Detalle: {error_msg}"
