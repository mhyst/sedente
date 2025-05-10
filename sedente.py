#!/usr/bin/env python3

import tkinter as tk
from datetime import datetime, timedelta
import threading
import time
from PIL import Image, ImageTk
from playsound import playsound
from database import Database
from models import SessionModel, BreakModel

class GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sedente")
        
        # Dichoso icono
        im = Image.open('icono.png')
        photo = ImageTk.PhotoImage(im)
        root.wm_iconphoto(True, photo)
        
        # Centrar la ventana
        window_width = 435
        window_height = 315

        root.geometry(f'{window_width}x{window_height}')

        self.root.resizable(False, False)

        self.outer_frame = tk.Frame(self.root)
        self.outer_frame.pack(padx=35, pady=35, expand=True, fill="both")

        self.estado = "trabajo"  # "trabajo", "pausa", "esperando_pausa"
        self.inicio_sesion = datetime.now()
        self.inicio_pausa = None
        self.siguiente_pausa = datetime.now() + timedelta(hours=2)

        # Widgets
        self.label_tiempo = tk.Label(self.outer_frame, text="", font=("Helvetica", 18))
        self.label_tiempo.pack(pady=10)

        self.label_estado = tk.Label(self.outer_frame, text="Estado: Trabajo", font=("Helvetica", 12))
        self.label_estado.pack(pady=5)

        self.btn_pausar = tk.Button(self.outer_frame, text="Hacer pausa ahora", command=self.iniciar_pausa)
        self.btn_pausar.pack(pady=5)

        self.btn_fin_pausa = tk.Button(self.outer_frame, text="Fin de la pausa", command=self.fin_pausa, state="disabled")
        self.btn_fin_pausa.pack(pady=5)

        # Inicializamos la base de datos
        self.db = Database("sedente.db")
        self.db.init()
        self.session_model = SessionModel(self.db)
        self.break_model = BreakModel(self.db)            

        # Hilo para temporizador
        self.hilo = threading.Thread(target=self.temporizador, daemon=True)
        self.hilo.start()

    def actualizar_reloj(self):
        ahora = datetime.now()
        if self.estado == "trabajo":
            restante = self.siguiente_pausa - ahora
            minutos, segundos = divmod(int(restante.total_seconds()), 60)
            self.label_tiempo.config(text=f"{minutos:02d}:{segundos:02d} hasta la pausa")
        elif self.estado == "pausa":
            duracion = ahora - self.inicio_pausa
            minutos, segundos = divmod(int(duracion.total_seconds()), 60)
            self.label_tiempo.config(text=f"Pausa: {minutos:02d}:{segundos:02d}")

    def temporizador(self):
        while True:
            self.root.after(0, self.actualizar_reloj)

            if self.estado == "trabajo" and datetime.now() >= self.siguiente_pausa:
                self.root.after(0, self.mostrar_ventana_pausa)

            time.sleep(1)

    def aviso_voz(self):
        # Reproducir el aviso
        playsound("voz.mp3")

    def mostrar_ventana_pausa(self):
        if self.estado != "trabajo":
            return
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(100, lambda: self.root.attributes('-topmost', False))
        self.label_estado.config(text="Sugerencia: Es hora de pausar")
        self.estado = "esperando_pausa"

        #Aviso de voz
        self.aviso_voz()


    def iniciar_pausa(self):
        if self.estado == "trabajo" or self.estado == "esperando_pausa":
            self.estado = "pausa"
            self.inicio_pausa = datetime.now()
            self.label_estado.config(text="Estado: En pausa")
            self.btn_pausar.config(state="disabled")
            self.btn_fin_pausa.config(state="normal")

    def fin_pausa(self):
        if self.estado == "pausa":
            duracion = datetime.now() - self.inicio_pausa
            self.estado = "trabajo"
            self.siguiente_pausa = datetime.now() + timedelta(hours=2)
            self.label_estado.config(text=f"Estado: Trabajo")
            self.btn_pausar.config(state="normal")
            self.btn_fin_pausa.config(state="disabled")
            print(f"Pausa registrada: {duracion.total_seconds() // 60:.0f} min")

            # Guardar sesión y pausa en la base de datos
            session_start = self.inicio_sesion
            session_end = datetime.now() - timedelta(seconds=duracion.total_seconds())
            self.inicio_sesion = datetime.now() # Iniciamos nueva sesión
            
            with self.db:
                self.session_model.create_session(session_start, session_end)
                session_id = self.session_model.get_last_session_id()
                self.break_model.create_break(session_id, self.inicio_pausa, int(duracion.total_seconds()))

if __name__ == "__main__":
    root = tk.Tk()
    gui = GUI(root)
    try:
        # Correcta visualización en Windows
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    finally:
        root.mainloop()
