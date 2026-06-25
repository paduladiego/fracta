import tkinter as tk
from gui.theme import Theme

class LogPanel(tk.Frame):
    """
    Widget customizado que encapsula o painel de exibicao de logs do sistema.
    Possui suporte a rolagem automatica e tags coloridas baseadas no tipo de evento.
    """
    def __init__(self, parent):
        super().__init__(parent, bg=Theme.CARD)
        
        # Label superior indicando o painel de log
        self.label = tk.Label(
            self, text="Log de Execução", font=Theme.FONT_LABEL,
            bg=Theme.CARD, fg=Theme.MUTED
        )
        self.label.pack(anchor="w", padx=12, pady=(8, 0))
        
        # Container de texto e scrollbar
        self.text_container = tk.Frame(self, bg=Theme.CARD)
        self.text_container.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        
        # Scrollbar vertical
        self.scrollbar = tk.Scrollbar(self.text_container, bg=Theme.SURFACE, troughcolor=Theme.CARD)
        self.scrollbar.pack(side="right", fill="y")
        
        # Area de texto (Text)
        self.text_area = tk.Text(
            self.text_container,
            bg=Theme.SURFACE, fg=Theme.TEXT,
            font=Theme.FONT_MONO,
            relief="flat", wrap="word",
            yscrollcommand=self.scrollbar.set,
            state="disabled",
            padx=8, pady=8
        )
        self.text_area.pack(side="left", fill="both", expand=True)
        self.scrollbar.config(command=self.text_area.yview)
        
        # Configuração de tags de cores para formatação
        self.text_area.tag_config("error",   foreground=Theme.ERROR)
        self.text_area.tag_config("success", foreground=Theme.SUCCESS)
        self.text_area.tag_config("accent",  foreground=Theme.ACCENT)
        self.text_area.tag_config("muted",   foreground=Theme.MUTED)
        
    def write_log(self, message: str, tag: str = None) -> None:
        """
        Adiciona uma mensagem de log no painel.
        Autodetecta a tag (cor) apropriada se nenhuma for especificada.
        """
        self.text_area.configure(state="normal")
        
        # Autodetecção de tag por padrão
        if tag is None:
            if "[ERRO]" in message or "Fail" in message:
                tag = "error"
            elif "[OK]" in message or "[CONCLUIDO]" in message:
                tag = "success"
            elif "[INFO]" in message:
                tag = "accent"
            else:
                tag = ""
                
        if tag:
            self.text_area.insert("end", message + "\n", tag)
        else:
            self.text_area.insert("end", message + "\n")
            
        self.text_area.see("end")
        self.text_area.configure(state="disabled")

    def clear(self) -> None:
        """Limpa todo o conteudo do painel de log."""
        self.text_area.configure(state="normal")
        self.text_area.delete("1.0", "end")
        self.text_area.configure(state="disabled")
