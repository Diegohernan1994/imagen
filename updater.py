import requests

CURRENT_VERSION = "1.0.0"
VERSION_URL = "https://raw.githubusercontent.com/usuario/california-enhancer/main/version.json"

def check_for_updates():
    """
    Consulta un archivo ligero en la nube para verificar si hay una version mas nueva.
    Retorna (hay_actualizacion, nueva_version, enlace_descarga, notas)
    """
    try:
        response = requests.get(VERSION_URL, timeout=2)
        if response.status_code == 200:
            data = response.json()
            remote_version = data.get("version", "1.0.0")
            if remote_version > CURRENT_VERSION:
                return True, remote_version, data.get("download_url", ""), data.get("notes", "")
    except Exception:
        pass
    return False, CURRENT_VERSION, "", ""
