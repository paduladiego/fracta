from tkinter import ttk

class Theme:
    """
    Centraliza a paleta de cores, fontes e estilos visuais do Fracta.
    Segue a identidade visual Dark Mode elegante baseada em tons de roxo e cinza escuro.
    """
    # Paleta de Cores
    BG         = "#0f1117"     # Fundo principal da aplicação
    SURFACE    = "#1a1d27"     # Superfície de inputs e containers internos
    CARD       = "#22263a"     # Fundo de blocos de configuração e painéis
    ACCENT     = "#7c6af7"     # Roxo vibrante para destaque, botões e ações principais
    ACCENT_HOV = "#9d8ff8"     # Roxo mais claro para efeito de hover (passar o mouse)
    TEXT       = "#e8eaf0"     # Texto principal de alta legibilidade
    MUTED      = "#8892a4"     # Texto secundário ou desativado
    SUCCESS    = "#4caf7d"     # Verde indicador de sucesso
    ERROR      = "#f25f5c"     # Vermelho indicador de erro
    
    # Tipografia (Fontes)
    FONT_MAIN  = ("Segoe UI", 10)
    FONT_TITLE = ("Segoe UI", 18, "bold")
    FONT_LABEL = ("Segoe UI", 9)
    FONT_BOLD  = ("Segoe UI", 10, "bold")
    FONT_MONO  = ("Consolas", 9)

    @classmethod
    def apply_styles(cls, root):
        """
        Configura e aplica estilos globais para componentes ttk na janela do aplicativo.
        """
        style = ttk.Style(root)
        style.theme_use("clam")

        # Configuração da barra de progresso customizada
        style.configure(
            "Accent.Horizontal.TProgressbar",
            troughcolor=cls.CARD,
            background=cls.ACCENT,
            darkcolor=cls.ACCENT,
            lightcolor=cls.ACCENT,
            bordercolor=cls.CARD,
            thickness=8,
        )

        # Configuração estética das Abas (Notebook)
        style.configure(
            "TNotebook",
            background=cls.BG,
            borderwidth=0
        )
        style.configure(
            "TNotebook.Tab",
            background=cls.SURFACE,
            foreground=cls.MUTED,
            font=cls.FONT_LABEL,
            padding=[16, 6],
            bordercolor=cls.BG,
            lightcolor=cls.SURFACE,
            darkcolor=cls.SURFACE
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", cls.CARD), ("active", cls.BG)],
            foreground=[("selected", cls.ACCENT), ("active", cls.TEXT)]
        )
