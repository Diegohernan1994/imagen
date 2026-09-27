import os
import sys
import subprocess
import webbrowser
import time

def main():
    # Obtener el directorio donde se esta ejecutando el programa
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
    app_path = os.path.join(base_dir, "app.py")
    
    # Abrir el navegador en el puerto de Streamlit
    webbrowser.open("http://localhost:8501")
    
    # Iniciar streamlit como servidor web local
    import streamlit.web.cli as stcli
    sys.argv = ["streamlit", "run", app_path, "--global.developmentMode=false", "--server.headless=true", "--browser.serverAddress=localhost"]
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
