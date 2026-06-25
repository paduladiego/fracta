import tkinter as tk
from tkinter import filedialog
from gui.theme import Theme
from core.constants import SUPPORTED_EXTENSIONS

class FileRow(tk.Frame):
    """
    Componente visual reutilizavel similar ao FolderRow, mas configurado para
    a seleção de um arquivo de imagem individual (unidade) utilizando filtros de formato.
    """
    def __init__(self, parent, label_text: str, dialog_title: str):
        super().__init__(parent, bg=Theme.CARD)
        self.dialog_title = dialog_title
        
        self.var = tk.StringVar()
        
        # Configura layout do componente
        self.label = tk.Label(
            self, text=label_text, font=Theme.FONT_LABEL,
            bg=Theme.CARD, fg=Theme.MUTED, width=18, anchor="w"
        )
        self.label.pack(side="left", padx=(0, 8), pady=4)
        
        self.entry = tk.Entry(
            self, textvariable=self.var, font=Theme.FONT_MAIN,
            bg=Theme.SURFACE, fg=Theme.TEXT,
            insertbackground=Theme.TEXT, relief="flat"
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=4)
        
        self.browse_btn = tk.Button(
            self, text="Procurar", font=Theme.FONT_LABEL,
            bg=Theme.SURFACE, fg=Theme.ACCENT,
            activebackground=Theme.BG, activeforeground=Theme.ACCENT_HOV,
            relief="flat", cursor="hand2", padx=10, pady=4,
            command=self._browse_file
        )
        self.browse_btn.pack(side="right", pady=4)

    def _browse_file(self) -> None:
        """
        Abre o dialogo do sistema para seleção de uma unica imagem,
        filtrando pelas extensoes suportadas declaradas nas constantes.
        """
        # Formata o filtro de extensoes do Tkinter dinamicamente
        extensions_pattern = " ".join(f"*{ext}" for ext in SUPPORTED_EXTENSIONS)
        filetypes = [
            ("Imagens Suportadas", extensions_pattern),
            ("Todos os arquivos", "*.*")
        ]
        
        path = filedialog.askopenfilename(
            title=self.dialog_title,
            filetypes=filetypes
        )
        if path:
            self.var.set(path)

    def get(self) -> str:
        """Retorna o caminho do arquivo selecionado."""
        return self.var.get().strip()

    def set(self, value: str) -> None:
        """Define o caminho do arquivo de imagem."""
        self.var.set(value)
