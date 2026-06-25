import tkinter as tk
from tkinter import ttk
from gui.theme import Theme
from gui.widgets.log_panel import LogPanel
from gui.widgets.progress_bar import ProgressBar
from gui.tabs.grid_tab import GridTab
from gui.tabs.canvas_tab import CanvasTab
from gui.tabs.resize_tab import ResizeTab

class FractaApp(tk.Tk):
    """
    Janela principal do aplicativo Fracta.
    Controla o layout global, abas (Notebook), barra de progresso e painel de log unificados.
    """
    def __init__(self):
        super().__init__()
        self.title("Fracta — Image Grid & Resizer")
        self.geometry("740x700")
        self.minsize(650, 600)
        self.configure(bg=Theme.BG)
        self.resizable(True, True)
        
        # Aplica estilos personalizados do tema para componentes ttk
        Theme.apply_styles(self)
        
        # Monta a árvore de componentes visuais
        self._build_ui()

    def _build_ui(self) -> None:
        """
        Estrutura e posiciona os elementos na janela principal.
        """
        # Container principal com margem (padding) externa
        root_frame = tk.Frame(self, bg=Theme.BG)
        root_frame.pack(fill="both", expand=True, padx=24, pady=20)

        # 1. Cabeçalho (Header)
        header = tk.Frame(root_frame, bg=Theme.BG)
        header.pack(fill="x", pady=(0, 14))
        
        title_label = tk.Label(
            header, text="Fracta", font=Theme.FONT_TITLE,
            bg=Theme.BG, fg=Theme.ACCENT
        )
        title_label.pack(side="left")
        
        subtitle_label = tk.Label(
            header, text="  Image Grid & Resizer", font=("Segoe UI", 12),
            bg=Theme.BG, fg=Theme.MUTED
        )
        subtitle_label.pack(side="left", pady=(6, 0))

        # 2. Painel de Log e Progresso Globais (criados antes para serem passados para as abas)
        # Progress Bar na parte inferior
        self.progress_bar = ProgressBar(root_frame)
        
        # Log Panel na parte inferior
        self.log_panel = LogPanel(root_frame)

        # 3. Notebook (Gerenciador de Abas)
        notebook = ttk.Notebook(root_frame)
        notebook.pack(fill="both", expand=False, pady=(0, 16))

        # Instancia e insere as abas no Notebook
        self.grid_tab = GridTab(notebook, self.log_panel, self.progress_bar)
        self.canvas_tab = CanvasTab(notebook, self.log_panel, self.progress_bar)
        self.resize_tab = ResizeTab(notebook, self.log_panel, self.progress_bar)

        notebook.add(self.grid_tab, text="Cortar Grid")
        notebook.add(self.canvas_tab, text="Canvas Fit")
        notebook.add(self.resize_tab, text="Redimensionar")

        # Posiciona Barra de Progresso e Log abaixo do Notebook
        self.progress_bar.pack(fill="x", pady=(0, 12))
        self.log_panel.pack(fill="both", expand=True)

        # Mensagem inicial no log
        self.log_panel.write_log(
            "Fracta iniciado. Escolha um recurso nas abas acima e clique no botão para executar.",
            "accent"
        )
