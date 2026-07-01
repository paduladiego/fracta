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
from gui.tabs.video_tab import VideoTab
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

        # Seletor global de Ambiente (Imagens vs Vídeos)
        self.env_frame = tk.Frame(root_frame, bg=Theme.BG)
        self.env_frame.pack(fill="x", pady=(0, 14))

        self.env_var = tk.StringVar(value="images")

        self.env_img_btn = tk.Button(
            self.env_frame, text="IMAGENS", font=("Segoe UI", 10, "bold"),
            bg=Theme.ACCENT, fg="#ffffff", activebackground=Theme.ACCENT_HOV,
            activeforeground="#ffffff", relief="flat", cursor="hand2",
            padx=20, pady=8, bd=0,
            command=lambda: self._select_environment("images")
        )
        self.env_img_btn.pack(side="left", padx=(0, 10))

        self.env_vid_btn = tk.Button(
            self.env_frame, text="VÍDEOS", font=("Segoe UI", 10, "bold"),
            bg=Theme.SURFACE, fg=Theme.MUTED, activebackground=Theme.SURFACE,
            activeforeground=Theme.TEXT, relief="flat", cursor="hand2",
            padx=20, pady=8, bd=0,
            command=lambda: self._select_environment("videos")
        )
        self.env_vid_btn.pack(side="left")

        # Binds para feedback de hover dos botoes de ambiente
        self.env_img_btn.bind("<Enter>", lambda _: self._on_env_hover(self.env_img_btn, "images", True))
        self.env_img_btn.bind("<Leave>", lambda _: self._on_env_hover(self.env_img_btn, "images", False))
        self.env_vid_btn.bind("<Enter>", lambda _: self._on_env_hover(self.env_vid_btn, "videos", True))
        self.env_vid_btn.bind("<Leave>", lambda _: self._on_env_hover(self.env_vid_btn, "videos", False))

        # Botão Sobre no cabeçalho (requisitos de autoria/Microsoft Store)
        about_btn = tk.Button(
            header, text="Sobre", font=("Segoe UI", 9, "bold"),
            bg=Theme.SURFACE, fg=Theme.MUTED, activebackground=Theme.SURFACE,
            activeforeground=Theme.TEXT, relief="flat", cursor="hand2",
            padx=10, pady=2, bd=0,
            command=self._show_about_dialog
        )
        about_btn.pack(side="right", pady=(4, 0))
        
        # Binds para feedback de hover do botao Sobre
        about_btn.bind("<Enter>", lambda _: about_btn.config(bg=Theme.CARD, fg=Theme.TEXT))
        about_btn.bind("<Leave>", lambda _: about_btn.config(bg=Theme.SURFACE, fg=Theme.MUTED))

        # Botão Recursos no cabeçalho para checagem de dependencias
        resources_btn = tk.Button(
            header, text="Checar Recursos", font=("Segoe UI", 9, "bold"),
            bg=Theme.SURFACE, fg=Theme.MUTED, activebackground=Theme.SURFACE,
            activeforeground=Theme.TEXT, relief="flat", cursor="hand2",
            padx=10, pady=2, bd=0,
            command=self._show_resources_dialog
        )
        resources_btn.pack(side="right", padx=(0, 8), pady=(4, 0))
        
        # Binds para feedback de hover do botao Recursos
        resources_btn.bind("<Enter>", lambda _: resources_btn.config(bg=Theme.CARD, fg=Theme.TEXT))
        resources_btn.bind("<Leave>", lambda _: resources_btn.config(bg=Theme.SURFACE, fg=Theme.MUTED))

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
        self.video_tab = VideoTab(self.tab_container, self.log_panel, self.progress_bar)

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

        # Rodape com informacoes de autoria (empacotado na parte inferior para garantir visibilidade)
        footer_frame = tk.Frame(root_frame, bg=Theme.BG)
        footer_frame.pack(side="bottom", fill="x", pady=(8, 0))
        
        footer_label = tk.Label(
            footer_frame, text="Desenvolvido por Dula.One", font=("Segoe UI", 9, "italic"),
            bg=Theme.BG, fg=Theme.MUTED, cursor="hand2"
        )
        footer_label.pack(side="right")
        footer_label.bind("<Button-1>", lambda _: webbrowser.open("https://dula.one"))

        # Log Panel ocupa todo o espaco central restante
        self.log_panel.pack(fill="both", expand=True)

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

    def _select_environment(self, env: str) -> None:
        """
        Alterna entre o ambiente de processamento de imagens e o de vídeos.
        """
        self.env_var.set(env)
        
        if env == "images":
            # Atualiza botoes
            self.env_img_btn.config(bg=Theme.ACCENT, fg="#ffffff")
            self.env_vid_btn.config(bg=Theme.SURFACE, fg=Theme.MUTED)
            
            # Oculta tab de video
            self.video_tab.pack_forget()
            
            # Mostra navbar de imagens e a aba ativa
            self.nav_frame.pack(fill="x", pady=(0, 10), after=self.env_frame)
            self._select_tab(self.active_tab)
            self.log_panel.write_log("Ambiente de Imagens ativo.", "accent")
        else:
            # Atualiza botoes
            self.env_img_btn.config(bg=Theme.SURFACE, fg=Theme.MUTED)
            self.env_vid_btn.config(bg=Theme.ACCENT, fg="#ffffff")
            
            # Oculta navbar de imagens e abas de imagem
            self.nav_frame.pack_forget()
            for key, (tab_frame, _) in self.tabs.items():
                tab_frame.pack_forget()
                
            # Mostra tab de video
            self.video_tab.pack(fill="both", expand=True)
            self.log_panel.write_log("Ambiente de Vídeos ativo. Requer FFmpeg no sistema.", "accent")

    def _on_env_hover(self, btn, env: str, is_hover: bool) -> None:
        """
        Efeito de hover para os botoes de alternancia de ambiente.
        """
        if self.env_var.get() == env:
            return
            
        if is_hover:
            btn.config(bg=Theme.CARD, fg=Theme.TEXT)
        else:
            btn.config(bg=Theme.SURFACE, fg=Theme.MUTED)

    def _show_about_dialog(self) -> None:
        """
        Exibe uma janela modal com informacoes sobre o app, direitos autorais e links da Dula.One.
        """
        about_win = tk.Toplevel(self)
        about_win.title("Sobre o Fracta")
        about_win.geometry("450x380")
        about_win.resizable(False, False)
        about_win.configure(bg=Theme.BG)
        about_win.transient(self)  # Define como filha da janela principal
        about_win.grab_set()       # Janela modal
        
        # Centralizar em relacao a janela principal
        about_win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - about_win.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - about_win.winfo_height()) // 2
        about_win.geometry(f"+{x}+{y}")
        
        # Container principal com padding
        content = tk.Frame(about_win, bg=Theme.BG, padx=24, pady=20)
        content.pack(fill="both", expand=True)
        
        # Titulo do app
        title_lbl = tk.Label(
            content, text="Fracta", font=("Segoe UI", 24, "bold"),
            bg=Theme.BG, fg=Theme.ACCENT
        )
        title_lbl.pack(pady=(0, 2))
        
        # Versao do app
        version_lbl = tk.Label(
            content, text=f"Versão {APP_VERSION}", font=("Segoe UI", 10, "bold"),
            bg=Theme.BG, fg=Theme.TEXT
        )
        version_lbl.pack(pady=(0, 15))
        
        # Descricao do app
        desc_lbl = tk.Label(
            content, text="Ferramenta moderna de redimensionamento e fatiamento de imagens.",
            font=("Segoe UI", 10), bg=Theme.BG, fg=Theme.TEXT, wraplength=400, justify="center"
        )
        desc_lbl.pack(pady=(0, 15))
        
        # Container com informacoes detalhadas do editor
        info_frame = tk.Frame(content, bg=Theme.CARD, bd=1, relief="solid", highlightthickness=0, padx=15, pady=15)
        info_frame.pack(fill="x", pady=(0, 20))
        info_frame.config(highlightbackground=Theme.SURFACE, highlightcolor=Theme.SURFACE)
        
        developer_lbl = tk.Label(
            info_frame, text="Desenvolvido por: Dula.One", font=("Segoe UI", 10, "bold"),
            bg=Theme.CARD, fg=Theme.TEXT
        )
        developer_lbl.pack(anchor="w", pady=(0, 4))
        
        copyright_lbl = tk.Label(
            info_frame, text="Copyright © 2026 Dula.One. Todos os direitos reservados.",
            font=("Segoe UI", 9), bg=Theme.CARD, fg=Theme.MUTED
        )
        copyright_lbl.pack(anchor="w", pady=(0, 8))
        
        # Rodape de links uteis (Politica de Privacidade e Site)
        links_frame = tk.Frame(info_frame, bg=Theme.CARD)
        links_frame.pack(fill="x")
        
        site_link = tk.Label(
            links_frame, text="Website Oficial", font=("Segoe UI", 9, "underline"),
            bg=Theme.CARD, fg=Theme.ACCENT, cursor="hand2"
        )
        site_link.pack(side="left", padx=(0, 15))
        site_link.bind("<Button-1>", lambda _: webbrowser.open("https://dula.one"))
        
        privacy_link = tk.Label(
            links_frame, text="Política de Privacidade", font=("Segoe UI", 9, "underline"),
            bg=Theme.CARD, fg=Theme.ACCENT, cursor="hand2"
        )
        privacy_link.pack(side="left")
        privacy_link.bind("<Button-1>", lambda _: webbrowser.open("https://dula.one/privacy"))
        
        # Botao Fechar
        close_btn = tk.Button(
            content, text="Fechar", font=("Segoe UI", 10, "bold"),
            bg=Theme.ACCENT, fg="#ffffff", activebackground=Theme.ACCENT,
            activeforeground="#ffffff", relief="flat", cursor="hand2",
            padx=20, pady=6, bd=0, command=about_win.destroy
        )
        close_btn.pack(side="bottom", pady=(10, 0))

    def _show_resources_dialog(self) -> None:
        """
        Exibe um popup modal verificando dependencias do sistema como FFmpeg e FFprobe
        e fornecendo guias amigaveis de resolucao.
        """
        from core.video_processor import VideoProcessor
        ffmpeg_ok = VideoProcessor.check_ffmpeg()
        ffprobe_ok = VideoProcessor.check_ffprobe()
        
        res_win = tk.Toplevel(self)
        res_win.title("Checagem de Recursos do Sistema")
        res_win.geometry("500x420")
        res_win.resizable(False, False)
        res_win.configure(bg=Theme.BG)
        res_win.transient(self)
        res_win.grab_set()
        
        # Centralizar
        res_win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - res_win.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - res_win.winfo_height()) // 2
        res_win.geometry(f"+{x}+{y}")
        
        # Container
        content = tk.Frame(res_win, bg=Theme.BG, padx=24, pady=20)
        content.pack(fill="both", expand=True)
        
        # Titulo
        title_lbl = tk.Label(
            content, text="Recursos do Sistema", font=("Segoe UI", 16, "bold"),
            bg=Theme.BG, fg=Theme.TEXT
        )
        title_lbl.pack(anchor="w", pady=(0, 15))
        
        # Status do FFmpeg
        ffmpeg_frame = tk.Frame(content, bg=Theme.CARD, bd=1, relief="solid", highlightthickness=0, padx=12, pady=10)
        ffmpeg_frame.pack(fill="x", pady=(0, 8))
        ffmpeg_frame.config(highlightbackground=Theme.SURFACE, highlightcolor=Theme.SURFACE)
        
        ffmpeg_title = tk.Label(
            ffmpeg_frame, text="FFmpeg (Processamento de Vídeo)", font=("Segoe UI", 10, "bold"),
            bg=Theme.CARD, fg=Theme.TEXT
        )
        ffmpeg_title.pack(anchor="w")
        
        ffmpeg_status_text = "Disponível — Pronto para uso!" if ffmpeg_ok else "Ausente — Necessário para processar vídeos"
        ffmpeg_status_color = Theme.SUCCESS if ffmpeg_ok else "#ff5555"
        
        ffmpeg_status = tk.Label(
            ffmpeg_frame, text=ffmpeg_status_text, font=("Segoe UI", 9, "bold"),
            bg=Theme.CARD, fg=ffmpeg_status_color
        )
        ffmpeg_status.pack(anchor="w", pady=(2, 0))
        
        # Status do FFprobe
        ffprobe_frame = tk.Frame(content, bg=Theme.CARD, bd=1, relief="solid", highlightthickness=0, padx=12, pady=10)
        ffprobe_frame.pack(fill="x", pady=(0, 15))
        ffprobe_frame.config(highlightbackground=Theme.SURFACE, highlightcolor=Theme.SURFACE)
        
        ffprobe_title = tk.Label(
            ffprobe_frame, text="FFprobe (Metadados de Vídeo)", font=("Segoe UI", 10, "bold"),
            bg=Theme.CARD, fg=Theme.TEXT
        )
        ffprobe_title.pack(anchor="w")
        
        ffprobe_status_text = "Disponível — Pronto para uso!" if ffprobe_ok else "Ausente — Necessário para analisar duração"
        ffprobe_status_color = Theme.SUCCESS if ffprobe_ok else "#ff5555"
        
        ffprobe_status = tk.Label(
            ffprobe_frame, text=ffprobe_status_text, font=("Segoe UI", 9, "bold"),
            bg=Theme.CARD, fg=ffprobe_status_color
        )
        ffprobe_status.pack(anchor="w", pady=(2, 0))
        
        # Painel de Dicas / Instrucoes se faltar algo
        if not (ffmpeg_ok and ffprobe_ok):
            guide_frame = tk.Frame(content, bg=Theme.BG)
            guide_frame.pack(fill="x")
            
            guide_lbl = tk.Label(
                guide_frame, text="Como resolver (Recomendado para Windows):",
                font=("Segoe UI", 10, "bold"), bg=Theme.BG, fg=Theme.ACCENT
            )
            guide_lbl.pack(anchor="w", pady=(0, 4))
            
            inst_text = (
                "Abra o PowerShell do Windows e execute o comando abaixo para instalar\n"
                "automaticamente via gerenciador de pacotes nativo (Winget):"
            )
            inst_lbl = tk.Label(
                guide_frame, text=inst_text, font=("Segoe UI", 9),
                bg=Theme.BG, fg=Theme.TEXT, justify="left"
            )
            inst_lbl.pack(anchor="w", pady=(0, 6))
            
            # Caixa do comando com botao Copiar
            cmd_frame = tk.Frame(guide_frame, bg=Theme.SURFACE, padx=10, pady=8)
            cmd_frame.pack(fill="x", pady=(0, 10))
            
            cmd_text = "winget install Gyan.FFmpeg"
            cmd_lbl = tk.Label(
                cmd_frame, text=cmd_text, font=("Consolas", 10, "bold"),
                bg=Theme.SURFACE, fg=Theme.ACCENT
            )
            cmd_lbl.pack(side="left")
            
            def copy_cmd():
                self.clipboard_clear()
                self.clipboard_append(cmd_text)
                copy_btn.config(text="Copiado!", fg=Theme.SUCCESS)
                self.after(1500, lambda: copy_btn.config(text="Copiar", fg=Theme.ACCENT))
                
            copy_btn = tk.Button(
                cmd_frame, text="Copiar", font=("Segoe UI", 8, "bold"),
                bg=Theme.BG, fg=Theme.ACCENT, activebackground=Theme.SURFACE,
                activeforeground=Theme.TEXT, relief="flat", cursor="hand2",
                command=copy_cmd, padx=8, pady=2, bd=0
            )
            copy_btn.pack(side="right")
            
            warn_lbl = tk.Label(
                guide_frame, text="*Nota: Reinicie o Fracta após a instalação para carregar as alterações.",
                font=("Segoe UI", 8, "italic"), bg=Theme.BG, fg=Theme.MUTED
            )
            warn_lbl.pack(anchor="w")
        else:
            # Caso tudo esteja ok
            success_frame = tk.Frame(content, bg=Theme.BG)
            success_frame.pack(fill="both", expand=True, pady=10)
            
            success_lbl = tk.Label(
                success_frame, text="Parabéns! Todos os recursos necessários estão instalados e configurados corretamente. O aplicativo está pronto para operar vídeos e imagens em capacidade máxima.",
                font=("Segoe UI", 10), bg=Theme.BG, fg=Theme.TEXT, justify="center", wraplength=420
            )
            success_lbl.pack(pady=20)
            
        # Botao Fechar
        close_btn = tk.Button(
            content, text="Fechar", font=("Segoe UI", 10, "bold"),
            bg=Theme.ACCENT, fg="#ffffff", activebackground=Theme.ACCENT_HOV,
            activeforeground="#ffffff", relief="flat", cursor="hand2",
            padx=20, pady=6, bd=0, command=res_win.destroy
        )
        close_btn.pack(side="bottom", pady=(10, 0))

