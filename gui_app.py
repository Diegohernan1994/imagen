import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import io
import zipfile
from pathlib import Path
import cv2
from PIL import Image, ImageTk
from batch_enhancer import enhance_single_image

class EnhancerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("California Remodeling Photo Enhancer Pro")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        self.files_to_process = []
        self.processed_files = []
        
        self.setup_ui()
        
    def setup_ui(self):
        # Header Frame
        header = ttk.Frame(self.root, padding="15")
        header.pack(fill=tk.X)
        
        title = ttk.Label(header, text="California Remodeling Photo Enhancer Pro", font=("Helvetica", 16, "bold"))
        title.pack(anchor=tk.W)
        subtitle = ttk.Label(header, text="Mejora profesional masiva para Cocinas, Baños, Piscinas, Techos y Pavers", font=("Helvetica", 10))
        subtitle.pack(anchor=tk.W, pady=(2, 0))
        
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=15, pady=5)
        
        # Options Frame
        opts_frame = ttk.LabelFrame(self.root, text=" Configuracion ", padding="15")
        opts_frame.pack(fill=tk.X, padx=15, pady=5)
        
        # Preset selection
        ttk.Label(opts_frame, text="Categoria / Preset:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.preset_var = tk.StringVar(value="Auto-detectar")
        presets = ["Auto-detectar", "General", "Kitchen", "Bathroom", "Pool", "Roofing", "Pavers"]
        self.preset_combo = ttk.Combobox(opts_frame, textvariable=self.preset_var, values=presets, state="readonly", width=18)
        self.preset_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Mode selection
        ttk.Label(opts_frame, text="Motor:").grid(row=0, column=2, sticky=tk.W, padx=(20, 5), pady=5)
        self.mode_var = tk.StringVar(value="upscayl_ai")
        r1 = ttk.Radiobutton(opts_frame, text="Upscayl AI UltraSharp (Maxima Calidad)", variable=self.mode_var, value="upscayl_ai")
        r1.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        r2 = ttk.Radiobutton(opts_frame, text="Modo Rapido HDR (< 1 seg)", variable=self.mode_var, value="rapido")
        r2.grid(row=0, column=4, sticky=tk.W, padx=5, pady=5)
        
        # File Actions Frame
        actions_frame = ttk.Frame(self.root, padding="15")
        actions_frame.pack(fill=tk.X, padx=15)
        
        self.btn_select_files = ttk.Button(actions_frame, text="Seleccionar Fotos...", command=self.select_files)
        self.btn_select_files.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_select_folder = ttk.Button(actions_frame, text="Seleccionar Carpeta Completa...", command=self.select_folder)
        self.btn_select_folder.pack(side=tk.LEFT, padx=(0, 10))
        
        self.lbl_count = ttk.Label(actions_frame, text="0 fotos seleccionadas", font=("Helvetica", 10, "italic"))
        self.lbl_count.pack(side=tk.LEFT, padx=10)
        
        # List of files
        list_frame = ttk.Frame(self.root, padding="15")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15)
        
        self.tree = ttk.Treeview(list_frame, columns=("file", "status"), show="headings", height=8)
        self.tree.heading("file", text="Archivo")
        self.tree.heading("status", text="Estado")
        self.tree.column("file", width=550)
        self.tree.column("status", width=180, anchor=tk.CENTER)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Progress & Run Frame
        bottom_frame = ttk.Frame(self.root, padding="15")
        bottom_frame.pack(fill=tk.X, padx=15, pady=5)
        
        self.prog_bar = ttk.Progressbar(bottom_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.prog_bar.pack(fill=tk.X, pady=(0, 10))
        
        self.lbl_status = ttk.Label(bottom_frame, text="Listo para comenzar")
        self.lbl_status.pack(side=tk.LEFT)
        
        self.btn_save_zip = ttk.Button(bottom_frame, text="Guardar Todas en ZIP...", command=self.save_zip, state=tk.DISABLED)
        self.btn_save_zip.pack(side=tk.RIGHT, padx=(10, 0))
        
        self.btn_run = ttk.Button(bottom_frame, text="INICIAR PROCESAMIENTO", command=self.start_processing)
        self.btn_run.pack(side=tk.RIGHT)
        
    def select_files(self):
        files = filedialog.askopenfilenames(
            title="Selecciona una o mas fotos de remodelacion",
            filetypes=[("Imagenes", "*.jpg *.jpeg *.png *.webp *.bmp")]
        )
        if files:
            self.files_to_process = list(files)
            self.update_list()
            
    def select_folder(self):
        folder = filedialog.askdirectory(title="Selecciona la carpeta con proyectos")
        if folder:
            valid_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
            found = [str(f) for f in Path(folder).rglob("*") if f.is_file() and f.suffix.lower() in valid_exts]
            if found:
                self.files_to_process = found
                self.update_list()
            else:
                messagebox.showinfo("Sin imagenes", "No se encontraron imagenes compatibles en la carpeta seleccionada.")
                
    def update_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for f in self.files_to_process:
            self.tree.insert("", tk.END, values=(os.path.basename(f), "Pendiente"))
        self.lbl_count.config(text=f"{len(self.files_to_process)} fotos cargadas")
        self.btn_save_zip.config(state=tk.DISABLED)
        self.processed_files.clear()
        
    def start_processing(self):
        if not self.files_to_process:
            messagebox.showwarning("Atencion", "Primero selecciona fotos o una carpeta.")
            return
            
        self.btn_run.config(state=tk.DISABLED)
        self.btn_select_files.config(state=tk.DISABLED)
        self.btn_select_folder.config(state=tk.DISABLED)
        self.btn_save_zip.config(state=tk.DISABLED)
        
        threading.Thread(target=self.run_batch_worker, daemon=True).start()
        
    def run_batch_worker(self):
        total = len(self.files_to_process)
        out_dir = Path(os.getcwd()) / "output_desktop"
        out_dir.mkdir(exist_ok=True)
        
        self.processed_files.clear()
        mode = self.mode_var.get()
        preset_choice = self.preset_var.get()
        
        for idx, file_path in enumerate(self.files_to_process):
            item_id = self.tree.get_children()[idx]
            self.tree.set(item_id, "status", "Procesando...")
            self.lbl_status.config(text=f"Procesando [{idx+1}/{total}]: {os.path.basename(file_path)}")
            
            p = preset_choice
            if p == "Auto-detectar":
                nl = os.path.basename(file_path).lower()
                if any(k in nl for k in ["kitchen", "cocina"]):
                    p = "Kitchen"
                elif any(k in nl for k in ["bath", "baño"]):
                    p = "Bathroom"
                elif any(k in nl for k in ["pool", "piscina"]):
                    p = "Pool"
                elif any(k in nl for k in ["roof", "techo"]):
                    p = "Roofing"
                elif any(k in nl for k in ["paver", "patio"]):
                    p = "Pavers"
                else:
                    p = "General"
                    
            out_file = out_dir / (Path(file_path).stem + "_mejorada.jpg")
            ok, msg = enhance_single_image(file_path, out_file, mode=mode, preset=p)
            
            if ok and out_file.exists():
                self.tree.set(item_id, "status", "Completado")
                self.processed_files.append(str(out_file))
            else:
                self.tree.set(item_id, "status", "Error")
                
            self.prog_bar['value'] = ((idx + 1) / total) * 100
            
        self.lbl_status.config(text=f"Proceso finalizado! {len(self.processed_files)} de {total} fotos mejoradas.")
        self.btn_run.config(state=tk.NORMAL)
        self.btn_select_files.config(state=tk.NORMAL)
        self.btn_select_folder.config(state=tk.NORMAL)
        if self.processed_files:
            self.btn_save_zip.config(state=tk.NORMAL)
            messagebox.showinfo("Completado", f"Se completaron {len(self.processed_files)} fotos con exito.\nPuedes guardarlas en un archivo ZIP con el boton inferior.")
            
    def save_zip(self):
        if not self.processed_files:
            return
        save_path = filedialog.asksaveasfilename(
            title="Guardar archivo ZIP",
            defaultextension=".zip",
            filetypes=[("Archivo ZIP", "*.zip")],
            initialfile="fotos_remodeling_mejoradas.zip"
        )
        if save_path:
            with zipfile.ZipFile(save_path, "w", zipfile.ZIP_DEFLATED) as z:
                for f in self.processed_files:
                    z.write(f, arcname=os.path.basename(f))
            messagebox.showinfo("Guardado", f"Archivo ZIP guardado exitosamente en:\n{save_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = EnhancerApp(root)
    root.mainloop()
