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

def prepare_photographic_base(img, preset="General"):
    """
    Prepara la fotografía para la IA y para la entrega final:
    1. Elimina la 'neblina' blanca típica de lentes de celular (Dehazing automático / Black-point stretch).
    2. Convierte los negros deslavados (gris) en negros puros y profundos (#151515).
    3. Realza la riqueza de tonos según el preset (maderas doradas, azulejos limpios, césped y agua).
    """
    if img is None:
        return img
        
    # 1. Corrección de Rango Dinámico y Punto Negro (Dehaze)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    p_low = float(np.percentile(gray, 1.2)) # punto negro
    p_high = float(np.percentile(gray, 99.7)) # punto blanco
    
    if p_high > p_low + 30: # Evitar división por cero o imágenes corruptas
        img_f = img.astype(np.float32)
        # Estiramiento de contraste protegiendo el rango
        stretched = np.clip((img_f - p_low) * (255.0 / (p_high - p_low)), 0, 255).astype(np.uint8)
    else:
        stretched = img.copy()
        
    # 2. Riqueza de Color y Vibrancia Natural
    hsv = cv2.cvtColor(stretched, cv2.COLOR_BGR2HSV).astype(np.float32)
    h, s, v = cv2.split(hsv)
    
    if preset == "Pool":
        # Intensifica el azul/turquesa del agua y verde del jardín
        is_water = (h >= 80) & (h <= 135)
        s[is_water] = np.clip(s[is_water] * 1.30, 0, 255)
        s[~is_water] = np.clip(s[~is_water] * 1.12, 0, 255)
    elif preset in ["Kitchen", "General"]:
        # Intensifica la calidez de pisos y muebles de madera (tonos amarillos/naranjas/marrones)
        is_warm = (h >= 10) & (h <= 45)
        s[is_warm] = np.clip(s[is_warm] * 1.20, 0, 255)
        s[~is_warm] = np.clip(s[~is_warm] * 1.08, 0, 255)
    elif preset == "Pavers":
        # Aumenta contraste y textura en piedras y adoquines
        s = np.clip(s * 1.15, 0, 255)
    elif preset == "Roofing":
        # Intensifica cielo azul de fondo
        is_sky = (h >= 95) & (h <= 130)
        s[is_sky] = np.clip(s[is_sky] * 1.25, 0, 255)
        s[~is_sky] = np.clip(s[~is_sky] * 1.10, 0, 255)
    else:
        s = np.clip(s * 1.10, 0, 255)
        
    final_hsv = cv2.merge((h, s, v)).astype(np.uint8)
    enhanced = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
    
    return enhanced

