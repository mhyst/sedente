#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import threading
import time
from PIL import Image, ImageTk
from playsound import playsound
from database import Database
from models import SessionModel, BreakModel
import os

class GUI:
    def __init__(self, root):
        self.stop_event = threading.Event()

        self.root = root
        self.root.title("Sedente")
        
        # Configuración del tema oscuro
        self.root.configure(bg='#1a1a1a')
        style = ttk.Style()
        style.theme_use('clam')  # Tema más moderno
        style.configure('TNotebook', background='#1a1a1a')
        style.configure('TNotebook.Tab', background='#2d2d2d', foreground='white')
        style.map('TNotebook.Tab', background=[('selected', '#3d3d3d')])
        style.configure('TFrame', background='#1a1a1a')
        style.configure('TLabel', background='#1a1a1a', foreground='white')
        style.configure('TButton', background='#2d2d2d', foreground='white')
        style.map('TButton', background=[('active', '#3d3d3d')])
        
        # Icono
        im = Image.open('icono.png')
        photo = ImageTk.PhotoImage(im)
        root.wm_iconphoto(True, photo)
        
        window_width = 735
        window_height = 615
        self.root.geometry(f'{window_width}x{window_height}')
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Notebook con pestañas
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=0)
        
        # Pestaña Sesión
        self.outer_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.outer_frame, text="Sesión")
        
        # Pestañas de gráficas
        #self.graficas_tiempo = ttk.Frame(self.notebook)
        #self.notebook.add(self.graficas_tiempo, text="Tiempo hasta la pausa")
        
        #self.graficas_duracion = ttk.Frame(self.notebook)
        #self.notebook.add(self.graficas_duracion, text="Duración de la pausa")
        
        #self.graficas_cumplimiento = ttk.Frame(self.notebook)
        #self.notebook.add(self.graficas_cumplimiento, text="Cumplimiento")

        # Inicializar base de datos
        self.db = Database("sedente.db")
        self.db.init()
        self.session_model = SessionModel(self.db)
        self.break_model = BreakModel(self.db)
        self.generar_graficas_pausas()

        # Estado de la sesión
        self.estado = "trabajo"
        self.check_last_session()
        self.inicio_pausa = None
        self.siguiente_pausa = self.inicio_sesion + timedelta(hours=2)

        # Widgets en la pestaña Sesión
        self.label_tiempo = ttk.Label(
            self.outer_frame,
            text="",
            font=('Helvetica', 18, 'bold'),
            style='TLabel'
        )
        self.label_tiempo.pack(pady=(100,10))

        self.label_estado = ttk.Label(
            self.outer_frame,
            text="Estado: Trabajo",
            font=('Helvetica', 12, 'bold'),
            style='TLabel'
        )
        self.label_estado.pack(pady=5)

        # Botones en un frame separado
        self.frame_botones = ttk.Frame(self.outer_frame, style='TFrame')
        self.frame_botones.pack(pady=20)
        
        self.btn_pausar = ttk.Button(
            self.frame_botones,
            text="Hacer pausa ahora",
            command=self.iniciar_pausa,
            style='TButton'
        )
        self.btn_pausar.pack(side=tk.LEFT, padx=5)
        
        self.btn_fin_pausa = ttk.Button(
            self.frame_botones,
            text="Fin de la pausa",
            command=self.fin_pausa,
            state="disabled",
            style='TButton'
        )
        self.btn_fin_pausa.pack(side=tk.RIGHT, padx=5)

        # Contenedor para el botón de actualizar gráficas
        self.frame_actualizar = ttk.Frame(self.outer_frame, style='TFrame')
        self.frame_actualizar.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        # Botón de actualizar gráficas en la parte inferior
        self.btn_actualizar_graficas = ttk.Button(
            self.frame_actualizar,
            text="🔄 Actualizar Gráficas",
            command=self.actualizar_graficas,
            style='TButton'
        )
        self.btn_actualizar_graficas.pack(fill=tk.X, padx=10, pady=5)

        # Temporizador
        self.temporizador_id = None
        self.iniciar_temporizador()

    def iniciar_temporizador(self):
        self.temporizador_id = self.root.after(1000, self.temporizador)
    
    def generar_graficas_pausas(self):
        rows = []

        with self.db:

            query = """
                SELECT s.id, s.start_time, b.break_time, s.duration, b.duration
                FROM sessions s
                JOIN breaks b ON s.id = b.session_id
            """

            rows = self.db.fetchall(query)

        session_ids = []
        delay_until_break = []
        break_durations = []
        compliance = []

        for row in rows:
            sid, s_start, b_time, s_dur, b_dur = row
            try:
                s_start_dt = datetime.fromisoformat(s_start)
                b_time_dt = datetime.fromisoformat(b_time)
                delay = (b_time_dt - s_start_dt).total_seconds() / 60
                session_ids.append(sid)
                delay_until_break.append(delay)
                break_durations.append(b_dur / 60)
                compliance.append((delay <= 120) and (b_dur >= 600))
                compliance_pausas = [1 if b_dur >= 10 else 0 for b_dur in break_durations]
            except Exception as e:
                print(f"Error en sesión {sid}: {e}")

        # Crear figuras de matplotlib
        fig1, ax1 = plt.subplots()
        ax1.bar(
            session_ids,
            delay_until_break,
            color=["green" if d <= 120 else "red" for d in delay_until_break]
        )
        ax1.axhline(120, color='gray', linestyle='--', label="Límite ideal (120 min)")
        ax1.set_title("Tiempo hasta iniciar la pausa")
        ax1.set_xlabel("ID de sesión")
        ax1.set_ylabel("Minutos hasta la pausa")
        ax1.legend()

        fig2, ax2 = plt.subplots()
        ax2.bar(
            session_ids,
            break_durations,
            color=["green" if d >= 10 else "red" for d in break_durations]
        )
        ax2.axhline(10, color='gray', linestyle='--', label="Mínimo ideal (10 min)")
        ax2.set_title("Duración de las pausas")
        ax2.set_xlabel("ID de sesión")
        ax2.set_ylabel("Duración (min)")
        ax2.legend()

        fig3, ax3 = plt.subplots()
        cumple = sum(compliance_pausas)
        no_cumple = len(compliance_pausas) - cumple
        ax3.pie([cumple, no_cumple], labels=["Cumple", "No cumple"], colors=["green", "red"], autopct='%1.1f%%')
        ax3.set_title("Cumplimiento de pausas saludables")

        # Función para agregar el canvas a un tab
        def agregar_canvas(fig, tab_title):
            # Buscar si ya existe una pestaña con ese título
            existing_tabs = self.notebook.tabs()
            tab_frame = None

            for tab_id in existing_tabs:
                if self.notebook.tab(tab_id, 'text') == tab_title:
                    tab_frame = self.notebook.nametowidget(tab_id)
                    break

            # Si no existe, crear una nueva pestaña con su frame
            if tab_frame is None:
                tab_frame = ttk.Frame(self.notebook)
                self.notebook.add(tab_frame, text=tab_title)
            else:
                # Si ya existe, destruir su contenido anterior
                for widget in tab_frame.winfo_children():
                    widget.destroy()

            # Crear y añadir el nuevo canvas
            canvas = FigureCanvasTkAgg(fig, master=tab_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Agregar los canvas al notebook
        agregar_canvas(fig1, 'Tiempo hasta pausa')
        agregar_canvas(fig2, 'Duración de la pausa')
        agregar_canvas(fig3, 'Cumplimiento')

    def actualizar_graficas(self):
        self.generar_graficas_pausas()

    def store_current_session(self):
        # Obtener la hora actual y guardarla en la tabla settings dentro de un bloque with
        
        with self.db:
            query = "INSERT OR REPLACE INTO settings (key, value) VALUES ('last_session_start', ?)"
            self.db.execute(query, (self.inicio_sesion.isoformat(),))

            query = "INSERT OR REPLACE INTO settings (key, value) VALUES ('last_state', ?)"
            self.db.execute(query, (self.estado,))

        print(f"Hora de inicio de sesión guardada: {self.inicio_sesion} {self.estado}")

    def check_last_session(self):
        result = []
        estado = ""
        # Recuperar la hora de inicio de la última sesión dentro de un bloque with
        with self.db:
            query = "SELECT value FROM settings WHERE key = 'last_session_start'"
            result = self.db.fetchall(query)

            query = "SELECT value FROM settings WHERE key = 'last_state'"
            result2 = self.db.fetchall(query)
            if result2:
                estado = result2[0][0]

        
        if result:
            # Si existe la clave, obtener la hora de inicio
            start_time_str = result[0][0]
            start_time = datetime.fromisoformat(start_time_str)
            now = datetime.now()
            tiempo_transcurrido = now - start_time

            if tiempo_transcurrido < timedelta(hours=2) and estado == "trabajo":
                self.inicio_sesion = start_time
                # Si la sesión tiene menos de 2 horas, continuar la sesión
                print(f"Sesión continúa. La última sesión comenzó hace {tiempo_transcurrido}.")
                # Aquí puedes incluir la lógica para continuar la sesión (e.g., asignar una pausa, etc.)
            else:
                # Si la sesión es demasiado antigua, eliminarla y crear una nueva
                print(f"Sesión demasiado antigua. Se ignorará la sesión y se iniciará una nueva.")
                self.inicio_sesion = datetime.now()
        else:
            # Si no existe el registro en la tabla settings (es decir, nunca se guardó la hora de inicio), iniciar una nueva sesión
            print("No se encontró información de la sesión anterior. Iniciando nueva sesión.")
            self.inicio_sesion = datetime.now()

    def on_close(self):
        self.store_current_session()
        self.stop_event.set()

        if self.temporizador_id is not None:
            self.root.after_cancel(self.temporizador_id)
        
        self.root.quit()
        self.root.destroy()

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
        if self.stop_event.is_set():
            return

        self.root.after(0, self.actualizar_reloj)

        if self.estado == "trabajo" and datetime.now() >= self.siguiente_pausa:
            self.mostrar_ventana_pausa()

        self.temporizador_id = self.root.after(1000, self.temporizador)

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
        if os.name == "nt":
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
    finally:
        root.mainloop()
