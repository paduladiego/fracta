import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import threading
from gui.theme import Theme
from gui.widgets.folder_row import FolderRow
from gui.widgets.file_row import FileRow
from core.grid_cutter import GridCutter

class GridTab(tk.Frame):
    """
    Aba que implementa a interface e controle para a funcionalidade de Cortar Grid.
    Suporta fatiamento de pastas em lote ou de imagens unicas (por unidade).
    """
    def __init__(self, parent, log_panel, progress_bar):
        super().__init__(parent, bg=Theme.CARD)
        self.log_panel = log_panel
        self.progress_bar = progress_bar

        # Container interno para espaçamento
        self.container = tk.Frame(self, bg=Theme.CARD)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        # 1. Seletor de Modo de Entrada (Lote vs Unidade)
        self.mode_var = tk.StringVar(value="folder")

        self.mode_frame = tk.Frame(self.container, bg=Theme.CARD)
        self.mode_frame.pack(fill="x", pady=(0, 8))

        tk.Label(
            self.mode_frame, text="Modo de Entrada:",
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
        ).pack(side="left", padx=(0, 10))

        self.radio_folder = tk.Radiobutton(
            self.mode_frame, text="Pasta (Lote)", variable=self.mode_var,
            value="folder", font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.TEXT,
            selectcolor=Theme.SURFACE, activebackground=Theme.CARD,
            activeforeground=Theme.TEXT, command=self._update_input_mode
        )
        self.radio_folder.pack(side="left", padx=10)

        self.radio_file = tk.Radiobutton(
            self.mode_frame, text="Imagem Única", variable=self.mode_var,
            value="file", font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.TEXT,
            selectcolor=Theme.SURFACE, activebackground=Theme.CARD,
            activeforeground=Theme.TEXT, command=self._update_input_mode
        )
        self.radio_file.pack(side="left", padx=10)

        # 2. Instancia ambos os seletores de entrada
        self.input_folder_row = FolderRow(
            self.container, 
            label_text="Pasta de entrada:", 
            dialog_title="Selecionar Pasta de Entrada"
        )
        self.input_folder_row.var.trace_add("write", self._on_folder_input_changed)

        self.input_file_row = FileRow(
            self.container, 
            label_text="Imagem de entrada:", 
            dialog_title="Selecionar Imagem de Entrada"
        )
        self.input_file_row.var.trace_add("write", self._on_file_input_changed)

        # 3. Seleção de pasta de saída (sempre visivel)
        self.output_row = FolderRow(
            self.container, 
            label_text="Pasta de saida:", 
            dialog_title="Selecionar Pasta de Saida"
        )

        # Define layout inicial
        self._update_input_mode()

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
            validate="key", validatecommand=vcmd,
            highlightthickness=1, highlightbackground="#2c2f3f",
            highlightcolor=Theme.ACCENT
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
            validate="key", validatecommand=vcmd,
            highlightthickness=1, highlightbackground="#2c2f3f",
            highlightcolor=Theme.ACCENT
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

    def _update_input_mode(self) -> None:
        """Altera dinamicamente os widgets de selecao conforme o modo de entrada."""
        self.input_folder_row.pack_forget()
        self.input_file_row.pack_forget()
        self.output_row.pack_forget()

        if self.mode_var.get() == "folder":
            self.input_folder_row.pack(fill="x", pady=6)
        else:
            self.input_file_row.pack(fill="x", pady=6)

        # Reposiciona o output sempre no final
        self.output_row.pack(fill="x", pady=6)

    def _on_folder_input_changed(self, *args) -> None:
        """Autopopula o campo de saída com a subpasta 'output' da pasta selecionada."""
        in_dir = self.input_folder_row.get()
        if in_dir and not self.output_row.get():
            self.output_row.set(str(Path(in_dir) / "output"))

    def _on_file_input_changed(self, *args) -> None:
        """Autopopula o campo de saída com a subpasta 'output' na pasta da imagem selecionada."""
        in_file = self.input_file_row.get()
        if in_file and not self.output_row.get():
            self.output_row.set(str(Path(in_file).parent / "output"))

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
        """Inicia a operação de fatiamento (grade) na thread secundaria."""
        mode = self.mode_var.get()
        output_dir = self.output_row.get()

        if not output_dir:
            messagebox.showwarning("Atenção", "Selecione a pasta de saída.")
            return

        # Validação do grid
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
            self.after(0, lambda m=msg: self.log_panel.write_log(m))

        def completion_handler(success):
            def _ui_update():
                self.run_btn.config(state="normal", text="Cortar Imagens")
                self.progress_bar.set_progress(100)
                if success:
                    messagebox.showinfo("Concluído", "Processamento concluído com sucesso!")
            self.after(0, _ui_update)

        # Instancia o processador orientado a objetos
        cutter = GridCutter(
            rows=rows,
            cols=cols,
            log_fn=log_handler,
            progress_fn=self.progress_bar.set_progress,
            done_fn=completion_handler
        )

        if mode == "folder":
            input_path = self.input_folder_row.get()
            if not input_path:
                messagebox.showwarning("Atenção", "Selecione a pasta de entrada.")
                self.run_btn.config(state="normal")
                return
            if not Path(input_path).is_dir():
                messagebox.showerror("Erro", f"Pasta de entrada não encontrada:\n{input_path}")
                self.run_btn.config(state="normal")
                return
            target_fn = cutter.process_batch
            target_args = (input_path, output_dir)
        else:
            input_path = self.input_file_row.get()
            if not input_path:
                messagebox.showwarning("Atenção", "Selecione a imagem de entrada.")
                self.run_btn.config(state="normal")
                return
            if not Path(input_path).is_file():
                messagebox.showerror("Erro", f"Imagem de entrada não encontrada:\n{input_path}")
                self.run_btn.config(state="normal")
                return
            target_fn = cutter.process_single
            target_args = (input_path, output_dir)

        # Dispara thread assíncrona para não travar a GUI
        thread = threading.Thread(
            target=target_fn,
            args=target_args,
            daemon=True
        )
        thread.start()
