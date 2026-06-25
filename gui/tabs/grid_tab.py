import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import threading
from gui.theme import Theme
from gui.widgets.folder_row import FolderRow
from core.grid_cutter import process_grid_folder

class GridTab(tk.Frame):
    """
    Aba que implementa a interface e controle para a funcionalidade de Cortar Grid.
    """
    def __init__(self, parent, log_panel, progress_bar):
        super().__init__(parent, bg=Theme.CARD)
        self.log_panel = log_panel
        self.progress_bar = progress_bar

        # Container interno para espaçamento
        self.container = tk.Frame(self, bg=Theme.CARD)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        # Seleção de pasta de entrada
        self.input_row = FolderRow(
            self.container, 
            label_text="Pasta de entrada:", 
            dialog_title="Selecionar Pasta de Entrada"
        )
        self.input_row.pack(fill="x", pady=6)
        self.input_row.var.trace_add("write", self._on_input_changed)

        # Seleção de pasta de saída
        self.output_row = FolderRow(
            self.container, 
            label_text="Pasta de saida:", 
            dialog_title="Selecionar Pasta de Saida"
        )
        self.output_row.pack(fill="x", pady=6)

        # Container de configurações adicionais (Grid)
        self.grid_config_frame = tk.Frame(self.container, bg=Theme.CARD)
        self.grid_config_frame.pack(fill="x", pady=(14, 0))

        tk.Label(
            self.grid_config_frame, text="Grid (Linhas x Colunas):",
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
        ).pack(side="left")

        # Validador para aceitar apenas numeros inteiros
        vcmd = (self.register(self._validate_int), "%P")

        self.rows_var = tk.StringVar(value="2")
        self.rows_entry = tk.Entry(
            self.grid_config_frame, textvariable=self.rows_var, width=4,
            font=Theme.FONT_MAIN, bg=Theme.SURFACE, fg=Theme.TEXT,
            insertbackground=Theme.TEXT, relief="flat",
            validate="key", validatecommand=vcmd
        )
        self.rows_entry.pack(side="left", padx=(10, 4))

        tk.Label(
            self.grid_config_frame, text="x", font=("Segoe UI", 14, "bold"),
            bg=Theme.CARD, fg=Theme.ACCENT
        ).pack(side="left", padx=2)

        self.cols_var = tk.StringVar(value="2")
        self.cols_entry = tk.Entry(
            self.grid_config_frame, textvariable=self.cols_var, width=4,
            font=Theme.FONT_MAIN, bg=Theme.SURFACE, fg=Theme.TEXT,
            insertbackground=Theme.TEXT, relief="flat",
            validate="key", validatecommand=vcmd
        )
        self.cols_entry.pack(side="left", padx=(4, 12))

        # Texto reativo que exibe um preview da quantidade de fatias
        self.preview_label = tk.Label(
            self.grid_config_frame, text="", font=Theme.FONT_LABEL,
            bg=Theme.CARD, fg=Theme.MUTED
        )
        self.preview_label.pack(side="left")

        self.rows_var.trace_add("write", lambda *_: self._update_preview())
        self.cols_var.trace_add("write", lambda *_: self._update_preview())
        self._update_preview()

        # Botão de Ação
        self.action_frame = tk.Frame(self.container, bg=Theme.CARD)
        self.action_frame.pack(fill="x", pady=(20, 0))

        self.run_btn = tk.Button(
            self.action_frame,
            text="Cortar Imagens",
            font=Theme.FONT_BOLD,
            bg=Theme.ACCENT, fg="#ffffff",
            activebackground=Theme.ACCENT_HOV,
            activeforeground="#ffffff",
            relief="flat", cursor="hand2",
            padx=24, pady=8,
            command=self._start_processing
        )
        self.run_btn.pack(side="left")
        self.run_btn.bind("<Enter>", lambda _: self.run_btn.config(bg=Theme.ACCENT_HOV))
        self.run_btn.bind("<Leave>", lambda _: self.run_btn.config(bg=Theme.ACCENT))

    def _on_input_changed(self, *args) -> None:
        """Autopopula o campo de saída com a subpasta 'output'."""
        in_dir = self.input_row.get()
        if in_dir and not self.output_row.get():
            self.output_row.set(str(Path(in_dir) / "output"))

    @staticmethod
    def _validate_int(value: str) -> bool:
        """Validador para inputs numericos inteiros positivos."""
        return value == "" or (value.isdigit() and int(value) >= 0)

    def _update_preview(self) -> None:
        """Atualiza a mensagem de preview da quantidade total de cortes."""
        try:
            r = int(self.rows_var.get() or 0)
            c = int(self.cols_var.get() or 0)
            if r > 0 and c > 0:
                total_slices = r * c
                self.preview_label.config(
                    text=f"-> {total_slices} fatia(s) por imagem",
                    fg=Theme.SUCCESS if total_slices <= 100 else Theme.ERROR
                )
            else:
                self.preview_label.config(text="", fg=Theme.MUTED)
        except ValueError:
            self.preview_label.config(text="", fg=Theme.MUTED)

    def _start_processing(self) -> None:
        """Inicia a operação de corte de grade de imagens em lote."""
        input_dir = self.input_row.get()
        output_dir = self.output_row.get()

        # Validações dos campos de pastas e valores
        if not input_dir:
            messagebox.showwarning("Atenção", "Selecione a pasta de entrada.")
            return
        if not output_dir:
            messagebox.showwarning("Atenção", "Selecione a pasta de saída.")
            return
        if not Path(input_dir).is_dir():
            messagebox.showerror("Erro", f"Pasta de entrada não encontrada:\n{input_dir}")
            return

        rows_str = self.rows_var.get()
        cols_str = self.cols_var.get()

        if not rows_str or not cols_str or int(rows_str) < 1 or int(cols_str) < 1:
            messagebox.showwarning("Atenção", "Informe valores de linha e coluna maiores que 0.")
            return

        rows = int(rows_str)
        cols = int(cols_str)

        # Desativa controles visuais durante processamento
        self.run_btn.config(state="disabled", text="Processando...")
        self.progress_bar.reset()
        self.log_panel.clear()

        def log_handler(msg):
            # Garante que os logs rodem de forma segura na thread principal
            self.after(0, lambda m=msg: self.log_panel.write_log(m))

        def completion_handler(success):
            def _ui_update():
                self.run_btn.config(state="normal", text="Cortar Imagens")
                self.progress_bar.set_progress(100)
                if success:
                    messagebox.showinfo("Concluído", "Todas as imagens foram cortadas com sucesso!")
            self.after(0, _ui_update)

        # Dispara thread assíncrona para não travar a GUI
        thread = threading.Thread(
            target=process_grid_folder,
            args=(
                input_dir, 
                output_dir, 
                rows, 
                cols, 
                log_handler, 
                self.progress_bar.set_progress, 
                completion_handler
            ),
            daemon=True
        )
        thread.start()
