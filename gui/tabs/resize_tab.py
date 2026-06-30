import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import threading
from gui.theme import Theme
from gui.widgets.folder_row import FolderRow
from gui.widgets.file_row import FileRow
from core.image_resizer import ImageResizer

class ResizeTab(tk.Frame):
    """
    Aba que implementa a interface e controle para a funcionalidade de Redimensionar Imagens.
    Permite processamento em lote ou imagem unica mantendo proporcoes.
    """
    def __init__(self, parent, log_panel, progress_bar):
        super().__init__(parent, bg=Theme.CARD)
        self.log_panel = log_panel
        self.progress_bar = progress_bar

        # Container interno
        self.container = tk.Frame(self, bg=Theme.CARD)
        self.container.pack(fill="both", expand=True, padx=20, pady=16)

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

        # 2. Instancia seletores de entrada
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

        # 3. Seleção de pasta de saída
        self.output_row = FolderRow(
            self.container, 
            label_text="Pasta de saida:", 
            dialog_title="Selecionar Pasta de Saida"
        )

        # Define layout inicial
        self._update_input_mode()

        # Configurações adicionais
        dims_frame = tk.Frame(self.container, bg=Theme.CARD)
        dims_frame.pack(fill="x", pady=10)

        vcmd = (self.register(self._validate_int_or_auto), "%P")

        tk.Label(
            dims_frame, text="Tamanho Alvo (L x A):",
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
        ).grid(row=0, column=0, sticky="w", pady=4)

        target_size_frame = tk.Frame(dims_frame, bg=Theme.CARD)
        target_size_frame.grid(row=0, column=1, sticky="w", padx=10, pady=4)

        self.width_var = tk.StringVar(value="500")
        self.width_entry = tk.Entry(
            target_size_frame, textvariable=self.width_var, width=6,
            font=Theme.FONT_MAIN, bg=Theme.SURFACE, fg=Theme.TEXT,
            insertbackground=Theme.TEXT, relief="flat",
            validate="key", validatecommand=vcmd,
            highlightthickness=1, highlightbackground="#2c2f3f",
            highlightcolor=Theme.ACCENT
        )
        self.width_entry.pack(side="left")

        self.width_auto = tk.BooleanVar(value=False)
        self.width_cb = tk.Checkbutton(
            target_size_frame, text="AUTO", variable=self.width_auto,
            font=Theme.FONT_LABEL, bg=Theme.SURFACE, fg=Theme.MUTED,
            selectcolor=Theme.ACCENT, activebackground=Theme.ACCENT_HOV,
            activeforeground="#ffffff", relief="flat", cursor="hand2",
            indicatoron=False, padx=8, pady=3, bd=0,
            command=self._toggle_width
        )
        self.width_cb.pack(side="left", padx=(4, 10))

        tk.Label(
            target_size_frame, text="x", font=Theme.FONT_BOLD,
            bg=Theme.CARD, fg=Theme.ACCENT
        ).pack(side="left", padx=2)

        self.height_var = tk.StringVar(value="AUTO")
        self.height_entry = tk.Entry(
            target_size_frame, textvariable=self.height_var, width=6,
            font=Theme.FONT_MAIN, bg=Theme.SURFACE, fg=Theme.TEXT,
            insertbackground=Theme.TEXT, relief="flat",
            validate="key", validatecommand=vcmd, state="disabled",
            highlightthickness=1, highlightbackground="#2c2f3f",
            highlightcolor=Theme.ACCENT
        )
        self.height_entry.pack(side="left")

        self.height_auto = tk.BooleanVar(value=True)
        self.height_cb = tk.Checkbutton(
            target_size_frame, text="AUTO", variable=self.height_auto,
            font=Theme.FONT_LABEL, bg=Theme.SURFACE, fg=Theme.MUTED,
            selectcolor=Theme.ACCENT, activebackground=Theme.ACCENT_HOV,
            activeforeground="#ffffff", relief="flat", cursor="hand2",
            indicatoron=False, padx=8, pady=3, bd=0,
            command=self._toggle_height
        )
        self.height_cb.pack(side="left", padx=(4, 4))
        tk.Label(target_size_frame, text="px", font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED).pack(side="left", padx=4)

        tk.Label(
            dims_frame, text="Sufixo de Saida:",
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
        ).grid(row=1, column=0, sticky="w", pady=6)

        suffix_frame = tk.Frame(dims_frame, bg=Theme.CARD)
        suffix_frame.grid(row=1, column=1, sticky="w", padx=10, pady=6)

        self.suffix_var = tk.StringVar(value="-fracta")
        self.suffix_entry = tk.Entry(
            suffix_frame, textvariable=self.suffix_var, width=12,
            font=Theme.FONT_MAIN, bg=Theme.SURFACE, fg=Theme.TEXT,
            insertbackground=Theme.TEXT, relief="flat",
            highlightthickness=1, highlightbackground="#2c2f3f",
            highlightcolor=Theme.ACCENT
        )
        self.suffix_entry.pack(side="left")

        self.preview_label = tk.Label(
            self.container, text="", font=Theme.FONT_LABEL,
            bg=Theme.CARD, fg=Theme.MUTED
        )
        self.preview_label.pack(anchor="w", pady=(8, 14))

        self.width_var.trace_add("write", lambda *_: self._update_preview())
        self.height_var.trace_add("write", lambda *_: self._update_preview())
        self.width_auto.trace_add("write", lambda *_: self._update_preview())
        self.height_auto.trace_add("write", lambda *_: self._update_preview())
        self._update_preview()

        # Botão de Ação
        self.action_frame = tk.Frame(self.container, bg=Theme.CARD)
        self.action_frame.pack(fill="x")

        self.run_btn = tk.Button(
            self.action_frame,
            text="Redimensionar Imagens",
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

        # Traces para atualizar o estilo visual dos chips AUTO (contraste de texto e fundo)
        self.width_auto.trace_add("write", lambda *_: self._update_chip_styles())
        self.height_auto.trace_add("write", lambda *_: self._update_chip_styles())
        self._update_chip_styles()

    def _update_input_mode(self) -> None:
        """Altera a interface com base no modo de entrada ativo."""
        self.input_folder_row.pack_forget()
        self.input_file_row.pack_forget()
        self.output_row.pack_forget()

        if self.mode_var.get() == "folder":
            self.input_folder_row.pack(fill="x", pady=6)
        else:
            self.input_file_row.pack(fill="x", pady=6)

        self.output_row.pack(fill="x", pady=6)

    def _on_folder_input_changed(self, *args) -> None:
        in_dir = self.input_folder_row.get()
        if in_dir and not self.output_row.get():
            self.output_row.set(str(Path(in_dir) / "output"))

    def _on_file_input_changed(self, *args) -> None:
        in_file = self.input_file_row.get()
        if in_file and not self.output_row.get():
            self.output_row.set(str(Path(in_file).parent / "output"))

    @staticmethod
    def _validate_int_or_auto(value: str) -> bool:
        return value == "" or value == "AUTO" or (value.isdigit() and int(value) >= 0)

    def _toggle_width(self) -> None:
        if self.width_auto.get():
            self.width_entry.config(state="disabled")
            self.width_var.set("AUTO")
        else:
            self.width_entry.config(state="normal")
            self.width_var.set("500")

    def _toggle_height(self) -> None:
        if self.height_auto.get():
            self.height_entry.config(state="disabled")
            self.height_var.set("AUTO")
        else:
            self.height_entry.config(state="normal")
            self.height_var.set("500")

    def _update_preview(self) -> None:
        w_is_auto = self.width_auto.get()
        h_is_auto = self.height_auto.get()

        if w_is_auto and h_is_auto:
            self.preview_label.config(
                text="-> As imagens manterão o tamanho original (largura e altura automáticas).",
                fg=Theme.MUTED
            )
        elif w_is_auto:
            val = self.height_var.get()
            self.preview_label.config(
                text=f"-> Altura fixa em {val if val and val != 'AUTO' else '0'}px. Largura calculada proporcionalmente.",
                fg=Theme.SUCCESS
            )
        elif h_is_auto:
            val = self.width_var.get()
            self.preview_label.config(
                text=f"-> Largura fixa em {val if val and val != 'AUTO' else '0'}px. Altura calculada proporcionalmente.",
                fg=Theme.SUCCESS
            )
        else:
            w_val = self.width_var.get()
            h_val = self.height_var.get()
            self.preview_label.config(
                text=f"-> Redimensionamento fixo para {w_val}x{h_val}px (pode distorcer a imagem original).",
                fg=Theme.ERROR
            )

    def _start_processing(self) -> None:
        """Inicia o processamento na thread secundaria."""
        mode = self.mode_var.get()
        output_dir = self.output_row.get()

        if not output_dir:
            messagebox.showwarning("Atenção", "Selecione a pasta de saída.")
            return

        if mode == "folder":
            input_path = self.input_folder_row.get()
            if not input_path:
                messagebox.showwarning("Atenção", "Selecione a pasta de entrada.")
                return
            if not Path(input_path).is_dir():
                messagebox.showerror("Erro", f"Pasta de entrada não encontrada:\n{input_path}")
                return
            target_method = "process_batch"
        else:
            input_path = self.input_file_row.get()
            if not input_path:
                messagebox.showwarning("Atenção", "Selecione a imagem de entrada.")
                return
            if not Path(input_path).is_file():
                messagebox.showerror("Erro", f"Imagem de entrada não encontrada:\n{input_path}")
                return
            target_method = "process_single"

        target_w = None
        if not self.width_auto.get():
            try:
                target_w = int(self.width_var.get())
                if target_w <= 0: raise ValueError
            except ValueError:
                messagebox.showwarning("Atenção", "Informe uma largura alvo numérica válida maior que 0.")
                return

        target_h = None
        if not self.height_auto.get():
            try:
                target_h = int(self.height_var.get())
                if target_h <= 0: raise ValueError
            except ValueError:
                messagebox.showwarning("Atenção", "Informe uma altura alvo numérica válida maior que 0.")
                return

        suffix_pattern = self.suffix_var.get().strip()

        # Desativa a UI e limpa painel
        self.run_btn.config(state="disabled", text="Processando...")
        self.progress_bar.reset()
        self.log_panel.clear()

        def log_handler(msg):
            self.after(0, lambda m=msg: self.log_panel.write_log(m))

        def completion_handler(success):
            def _ui_update():
                self.run_btn.config(state="normal", text="Redimensionar Imagens")
                self.progress_bar.set_progress(100)
                if success:
                    messagebox.showinfo("Concluído", "Redimensionamento concluído com sucesso!")
            self.after(0, _ui_update)

        # Instancia o processador orientado a objetos
        resizer = ImageResizer(
            target_w=target_w,
            target_h=target_h,
            suffix_pattern=suffix_pattern,
            log_fn=log_handler,
            progress_fn=self.progress_bar.set_progress,
            done_fn=completion_handler
        )

        target_fn = getattr(resizer, target_method)

        # Dispara thread
        thread = threading.Thread(
            target=target_fn,
            args=(input_path, output_dir),
            daemon=True
        )
        thread.start()

    def _update_chip_styles(self) -> None:
        """
        Atualiza a cor de fundo e texto dos chips AUTO de acordo com o estado selecionado
        para garantir contraste perfeito no Windows (evita texto cinza sobre roxo).
        """
        for cb, var in [(self.width_cb, self.width_auto), (self.height_cb, self.height_auto)]:
            if var.get():
                cb.config(bg=Theme.ACCENT, fg="#ffffff")
            else:
                cb.config(bg=Theme.SURFACE, fg=Theme.MUTED)
