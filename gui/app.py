import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import webbrowser
import threading
from gui.theme import Theme
from gui.widgets.log_panel import LogPanel
from gui.widgets.progress_bar import ProgressBar
from gui.tabs.grid_tab import GridTab
from gui.tabs.canvas_tab import CanvasTab
from gui.tabs.resize_tab import ResizeTab
from gui.tabs.autocrop_tab import AutocropTab
from gui.tabs.compress_tab import CompressTab
from core.constants import APP_VERSION

class FractaApp(tk.Tk):
    """
    Janela principal do aplicativo Fracta.
    Controla o layout global, abas (Notebook), barra de progresso e painel de log unificados.
    """
    @staticmethod
    def resource_path(relative_path: str) -> str:
        """
        Retorna o caminho absoluto para recursos, lidando com caminhos temporarios
        do PyInstaller (_MEIPASS) e desenvolvimento local.
        """
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def __init__(self):
        super().__init__()
        self.title(f"Fracta v{APP_VERSION} — Image Grid & Resizer")
        self.geometry("740x700")
        self.minsize(650, 600)
        self.configure(bg=Theme.BG)
        self.resizable(True, True)
        
        # Define o icone da barra de titulo do app (.ico no Windows, .png de fallback)
        icon_path_ico = self.resource_path("assets/logo-fracta.ico")
        icon_path_png = self.resource_path("assets/logo-fracta.png")
        
        icon_set = False
        if os.path.exists(icon_path_ico):
            try:
                self.iconbitmap(default=icon_path_ico)
                icon_set = True
            except Exception:
                pass
                
        if not icon_set and os.path.exists(icon_path_png):
            try:
                self.icon_img = ImageTk.PhotoImage(file=icon_path_png)
                self.iconphoto(True, self.icon_img)
            except Exception:
                pass

        # Aplica estilos personalizados do tema para componentes ttk
        Theme.apply_styles(self)
        
        # Monta a árvore de componentes visuais
        self._build_ui()
        
        # Dispara verificação silenciosa de atualizações remotas
        threading.Thread(target=self._check_for_updates, daemon=True).start()

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
        
        # Carrega e exibe o logo da Dula.One se existir
        logo_path = self.resource_path("assets/logo-fracta.png")
        logo_loaded = False
        if os.path.exists(logo_path):
            try:
                logo_img = Image.open(logo_path)
                aspect_ratio = logo_img.width / logo_img.height
                logo_h = 36
                logo_w = int(logo_h * aspect_ratio)
                logo_img = logo_img.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
                self.logo_tk = ImageTk.PhotoImage(logo_img)
                
                logo_label = tk.Label(header, image=self.logo_tk, bg=Theme.BG)
                logo_label.pack(side="left")
                logo_loaded = True
            except Exception:
                pass

        if not logo_loaded:
            title_label = tk.Label(
                header, text="Fracta", font=Theme.FONT_TITLE,
                bg=Theme.BG, fg=Theme.ACCENT
            )
            title_label.pack(side="left")
        
        subtitle_label = tk.Label(
            header, text=f"  v{APP_VERSION} — Image Grid & Resizer", font=("Segoe UI", 11),
            bg=Theme.BG, fg=Theme.MUTED
        )
        subtitle_label.pack(side="left", pady=(6, 0))

        # 2. Painel de Log e Progresso Globais (criados antes para serem passados para as abas)
        # Progress Bar na parte inferior
        self.progress_bar = ProgressBar(root_frame)
        
        # Log Panel na parte inferior
        self.log_panel = LogPanel(root_frame)

        # 3. Navbar Customizada (Pill Tabs)
        self.nav_frame = tk.Frame(root_frame, bg=Theme.BG)
        self.nav_frame.pack(fill="x", pady=(0, 10))

        # Container principal de conteúdo das abas
        self.tab_container = tk.Frame(
            root_frame, bg=Theme.CARD, bd=1, relief="solid", highlightthickness=0
        )
        self.tab_container.pack(fill="both", expand=True, pady=(0, 16))

        # Instancia as abas dentro do container de abas
        self.grid_tab = GridTab(self.tab_container, self.log_panel, self.progress_bar)
        self.canvas_tab = CanvasTab(self.tab_container, self.log_panel, self.progress_bar)
        self.resize_tab = ResizeTab(self.tab_container, self.log_panel, self.progress_bar)
        self.autocrop_tab = AutocropTab(self.tab_container, self.log_panel, self.progress_bar)
        self.compress_tab = CompressTab(self.tab_container, self.log_panel, self.progress_bar)

        # Configura o mapeamento das abas
        self.tabs = {
            "grid": (self.grid_tab, "Cortar Grid"),
            "canvas": (self.canvas_tab, "Canvas Fit"),
            "resize": (self.resize_tab, "Redimensionar"),
            "autocrop": (self.autocrop_tab, "Aparar Bordas"),
            "compress": (self.compress_tab, "Comprimir")
        }

        # Cria os botões da barra de navegação estilo cápsula
        self.nav_buttons = {}
        for key, (_, title) in self.tabs.items():
            btn = tk.Button(
                self.nav_frame, text=title, font=Theme.FONT_BOLD,
                bg=Theme.SURFACE, fg=Theme.MUTED, activebackground=Theme.SURFACE,
                activeforeground=Theme.TEXT, relief="flat", cursor="hand2",
                padx=16, pady=6, bd=0,
                command=lambda k=key: self._select_tab(k)
            )
            btn.pack(side="left", padx=(0, 8))
            # Binds para feedback de hover nos botões inativos
            btn.bind("<Enter>", lambda _, b=btn, k=key: self._on_tab_hover(b, k, True))
            btn.bind("<Leave>", lambda _, b=btn, k=key: self._on_tab_hover(b, k, False))
            self.nav_buttons[key] = btn

        # Seleciona a aba padrão na inicialização
        self._select_tab("grid")

        # Posiciona Barra de Progresso e Log abaixo do Container
        self.progress_bar.pack(fill="x", pady=(0, 12))
        self.log_panel.pack(fill="both", expand=True)

        # Rodape com informacoes de autoria
        footer_frame = tk.Frame(root_frame, bg=Theme.BG)
        footer_frame.pack(fill="x", pady=(8, 0))
        
        footer_label = tk.Label(
            footer_frame, text="Desenvolvido por Dula.One", font=("Segoe UI", 9, "italic"),
            bg=Theme.BG, fg=Theme.MUTED, cursor="hand2"
        )
        footer_label.pack(side="right")
        footer_label.bind("<Button-1>", lambda _: webbrowser.open("https://dula.one"))

        # Mensagem inicial no log
        self.log_panel.write_log(
            "Fracta iniciado. Escolha um recurso nas abas acima e clique no botão para executar.",
            "accent"
        )

    def _check_for_updates(self) -> None:
        """
        Executa a checagem de atualizações de forma assíncrona.
        Se houver atualização, agenda a exibição na interface principal.
        """
        from core.updater import AppUpdater
        update_data = AppUpdater.check_for_updates(APP_VERSION)
        if update_data:
            self.after(0, lambda: self._show_update_notification(update_data))

    def _show_update_notification(self, update_data: dict) -> None:
        """
        Registra o aviso de atualização no log e abre popup oferecendo o download.
        """
        latest_ver = update_data["latest_version"]
        changelog = update_data["changelog"]
        download_url = update_data["download_url"]
        
        # Alerta visual no log central
        msg = (
            f"\n{'='*60}\n"
            f"[ATUALIZAÇÃO] Uma nova versão (v{latest_ver}) está disponível!\n"
            f"Novidades: {changelog}\n"
            f"Baixe a versão correspondente em: {download_url}\n"
            f"{'='*60}"
        )
        self.log_panel.write_log(msg, "accent")
        
        # Pop-up de diálogo
        ans = messagebox.askyesno(
            "Atualização Disponível",
            f"Uma nova versão (v{latest_ver}) do Fracta está disponível!\n\n"
            f"Novidades nesta versão:\n- {changelog}\n\n"
            f"Deseja abrir a página de download para atualizar agora?"
        )
        if ans:
            webbrowser.open(download_url)

    def _select_tab(self, tab_key: str) -> None:
        """
        Alterna a visibilidade das abas e destaca o botão ativo na Navbar.
        """
        self.active_tab = tab_key
        
        # Oculta todos os frames das abas e restaura o estilo padrão dos botões
        for key, (tab_frame, _) in self.tabs.items():
            tab_frame.pack_forget()
            btn = self.nav_buttons[key]
            btn.config(bg=Theme.SURFACE, fg=Theme.MUTED)
            
        # Mostra o frame correspondente à aba ativa e pinta o botão de roxo
        active_frame, _ = self.tabs[tab_key]
        active_frame.pack(fill="both", expand=True)
        
        active_btn = self.nav_buttons[tab_key]
        active_btn.config(bg=Theme.ACCENT, fg="#ffffff")

    def _on_tab_hover(self, btn, key: str, is_hover: bool) -> None:
        """
        Adiciona efeito visual de hover nos botões inativos da Navbar.
        """
        if hasattr(self, 'active_tab') and self.active_tab == key:
            return  # Não altera o estilo se o botão for a aba ativa
            
        if is_hover:
            btn.config(bg=Theme.CARD, fg=Theme.TEXT)
        else:
            btn.config(bg=Theme.SURFACE, fg=Theme.MUTED)

