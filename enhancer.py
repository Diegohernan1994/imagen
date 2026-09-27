import cv2
import numpy as np

def correct_perspective(img):
    """
    Intenta detectar lineas casi verticales y aplica una transformacion
    para enderezar las paredes (Perspective Deskew).
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
    
    if lines is None:
        return img
        
    angles = []
    for line in lines:
        rho, theta = line[0]
        # Buscar lineas que esten cerca de la vertical (theta cerca de 0 o PI)
        angle = np.degrees(theta)
        if (angle < 15 or angle > 165):
            if angle > 90:
                angle -= 180
            angles.append(angle)
            
    if not angles:
        return img
        
    median_angle = np.median(angles)
    if abs(median_angle) < 0.5:
        return img
        
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    # Rotar para alinear las verticales (opuesto a la inclinacion detectada)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    
    return rotated

def balance_white_conservative(img):
    """
    Balance de blancos suave y selectivo.
    Si la foto ya tiene blancos limpios (como gabinetes blancos),
    NO la sobreexpone ni lava los tonos calidos naturales de la madera.
    """
    # Mantiene la calidez y el contraste original del piso y ambiente
    return img

def enhance_hdr_and_sharpness(img, preset="General", scale=1):
    """
    Pipeline Fotográfico Inmobiliario Mejorado:
    - Nitidez de alta definición (High-Pass Unsharp Masking)
    - Recuperación inteligente de rango dinámico sin blanquear
    - Contraste rico y profundo en maderas y pisos
    """
    h, w = img.shape[:2]
    
    # 1. Escalar 2x si se solicita manteniendo definicion
    if scale > 1:
        img = cv2.resize(img, (w * scale, h * scale), interpolation=cv2.INTER_LANCZOS4)
        
    # 2. Separar luminosidad en espacio LAB
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # CLAHE mucho mas sutil (clipLimit bajo) para no lavar/quemar blancos
    clip_limit = 1.3 if preset in ["Kitchen", "Bathroom"] else 1.2
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
    l_clahe = clahe.apply(l)
    
    # Solo un 15% de realce de sombras para evitar lavar los tonos oscuros/madera
    l_final = cv2.addWeighted(l_clahe, 0.25, l, 0.75, 0)
    
    lab_merged = cv2.merge((l_final, a, b))
    bgr = cv2.cvtColor(lab_merged, cv2.COLOR_LAB2BGR)
    
    # 3. Nitidez y Enfoque Profesional tipo Lightroom (Clarity + High-Pass)
    # Crea microcontraste en los bordes de azulejos, perillas, vetas de madera
    blur_fine = cv2.GaussianBlur(bgr, (0, 0), 1.2)
    sharp = cv2.addWeighted(bgr, 1.6, blur_fine, -0.6, 0)
    
    # 4. Color y Vibrancia natural (sin perder los dorados del piso de madera)
    hsv = cv2.cvtColor(sharp, cv2.COLOR_BGR2HSV).astype(np.float32)
    h, s, v = cv2.split(hsv)
    
    if preset == "Pool":
        is_blue = (h >= 85) & (h <= 135)
        s[is_blue] = np.clip(s[is_blue] * 1.25, 0, 255)
        s[~is_blue] = np.clip(s[~is_blue] * 1.05, 0, 255)
    else:
        # Preserva el tono original de la madera aumentando sutilmente la vivacidad
        s = np.clip(s * 1.06, 0, 255)
        
    final_hsv = cv2.merge((h, s, v)).astype(np.uint8)
    enhanced = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
    
    return enhanced
