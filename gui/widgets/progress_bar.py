import tkinter as tk
from tkinter import ttk
from gui.theme import Theme

class ProgressBar(tk.Frame):
    """
    Widget customizado que contem uma barra de progresso ttk estilizada
    e um label mostrando a porcentagem atual da tarefa em execução.
    """
    def __init__(self, parent):
        super().__init__(parent, bg=Theme.BG)
        
        self.progress_var = tk.DoubleVar(value=0)
        
        # Barra de progresso horizontal
        self.bar = ttk.Progressbar(
            self,
            style="Accent.Horizontal.TProgressbar",
            variable=self.progress_var,
            maximum=100
        )
        self.bar.pack(fill="x")
        
        # Label reativo com a porcentagem
        self.pct_label = tk.Label(
            self, text="0%", font=Theme.FONT_LABEL,
            bg=Theme.BG, fg=Theme.MUTED
        )
        self.pct_label.pack(anchor="e", pady=(4, 0))

    def set_progress(self, value: float) -> None:
        """
        Define o valor do progresso de forma segura para threads (thread-safe).
        value deve ser um valor de 0 a 100.
        """
        # Garante que as alteracoes de UI rodem na main thread do tkinter
        self.after(0, lambda: self.progress_var.set(value))
        self.after(0, lambda: self.pct_label.config(text=f"{value:.0f}%"))

    def reset(self) -> None:
        """Reseta a barra de progresso para o estado inicial (0%)."""
        self.set_progress(0)
