import tkinter as tk
from tkinter import filedialog
from gui.theme import Theme

class FolderRow(tk.Frame):
    """
    Componente visual reutilizavel que agrupa um Label, um campo de entrada de texto (Entry)
    e um botao "Procurar" para seleção de diretorios.
    """
    def __init__(self, parent, label_text: str, dialog_title: str):
        super().__init__(parent, bg=Theme.CARD)
        self.dialog_title = dialog_title
        
        # Variavel reativa de texto
        self.var = tk.StringVar()
        
        # Configura layout interno usando pack
        self.label = tk.Label(
            self, text=label_text, font=Theme.FONT_LABEL,
            bg=Theme.CARD, fg=Theme.MUTED, width=18, anchor="w"
        )
        self.label.pack(side="left", padx=(0, 8), pady=4)
        
        self.entry = tk.Entry(
            self, textvariable=self.var, font=Theme.FONT_MAIN,
            bg=Theme.SURFACE, fg=Theme.TEXT,
            insertbackground=Theme.TEXT, relief="flat",
            highlightthickness=1, highlightbackground="#2c2f3f",
            highlightcolor=Theme.ACCENT
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=4)
        
        self.browse_btn = tk.Button(
            self, text="Procurar", font=Theme.FONT_LABEL,
            bg=Theme.SURFACE, fg=Theme.ACCENT,
            activebackground=Theme.BG, activeforeground=Theme.ACCENT_HOV,
            relief="flat", cursor="hand2", padx=10, pady=4,
            command=self._browse_directory
        )
        self.browse_btn.pack(side="right", pady=4)
        
        # Binds para efeito hover
        self.browse_btn.bind("<Enter>", lambda _: self.browse_btn.config(bg=Theme.ACCENT, fg="#ffffff"))
        self.browse_btn.bind("<Leave>", lambda _: self.browse_btn.config(bg=Theme.SURFACE, fg=Theme.ACCENT))

    def _browse_directory(self) -> None:
        """
        Abre o dialogo nativo do sistema para escolha de pastas.
        """
        path = filedialog.askdirectory(title=self.dialog_title)
        if path:
            self.var.set(path)

    def get(self) -> str:
        """Retorna o texto digitado ou selecionado na pasta (sem espacos em branco)."""
        return self.var.get().strip()

    def set(self, value: str) -> None:
        """Define o valor do campo de texto da pasta."""
        self.var.set(value)
