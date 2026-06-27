import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import threading
from gui.theme import Theme
from gui.widgets.folder_row import FolderRow
from gui.widgets.file_row import FileRow
from core.canvas_fitter import CanvasFitter

class CanvasTab(tk.Frame):
    """
    Aba que implementa a interface e controle para a funcionalidade de Canvas Fit.
    Suporta processamento em lote ou imagem unica, enquadrando-as com proporcao.
    """
    BG_COLORS = {
        "Transparente": (0, 0, 0, 0),
        "Branco": (255, 255, 255, 255),
        "Preto": (0, 0, 0, 255),
        "Verde (Chromakey)": (0, 255, 0, 255),
        "Azul (Chromakey)": (0, 0, 255, 255)
    }

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

        # Define layout inicial das pastas
        self._update_input_mode()

        # Frame de configurações de dimensão e parâmetros do Canvas
        dims_frame = tk.Frame(self.container, bg=Theme.CARD)
        dims_frame.pack(fill="x", pady=10)

        vcmd = (self.register(self._validate_int_or_auto), "%P")

        # 1. Canvas Externo (Fixo)
        tk.Label(
            dims_frame, text="Canvas Externo (L x A):",
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
        ).grid(row=0, column=0, sticky="w", pady=4)

        canvas_size_frame = tk.Frame(dims_frame, bg=Theme.CARD)
        canvas_size_frame.grid(row=0, column=1, sticky="w", padx=10, pady=4)

        self.canvas_w_var = tk.StringVar(value="800")
        self.canvas_w_entry = tk.Entry(
            canvas_size_frame, textvariable=self.canvas_w_var, width=6,
            font=Theme.FONT_MAIN, bg=Theme.SURFACE, fg=Theme.TEXT,
            insertbackground=Theme.TEXT, relief="flat",
            validate="key", validatecommand=vcmd,
            highlightthickness=1, highlightbackground="#2c2f3f",
            highlightcolor=Theme.ACCENT
        )
        self.canvas_w_entry.pack(side="left")

        tk.Label(
            canvas_size_frame, text="x", font=Theme.FONT_BOLD,
            bg=Theme.CARD, fg=Theme.ACCENT
        ).pack(side="left", padx=6)

        self.canvas_h_var = tk.StringVar(value="800")
        self.canvas_h_entry = tk.Entry(
            canvas_size_frame, textvariable=self.canvas_h_var, width=6,
            font=Theme.FONT_MAIN, bg=Theme.SURFACE, fg=Theme.TEXT,
            insertbackground=Theme.TEXT, relief="flat",
            validate="key", validatecommand=vcmd,
            highlightthickness=1, highlightbackground="#2c2f3f",
            highlightcolor=Theme.ACCENT
        )
        self.canvas_h_entry.pack(side="left")
        tk.Label(canvas_size_frame, text="px", font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED).pack(side="left", padx=4)


        # 2. Conteúdo Interno (Pode ser AUTO)
        tk.Label(
            dims_frame, text="Limite Interno (L x A):",
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
        ).grid(row=1, column=0, sticky="w", pady=4)

        inner_size_frame = tk.Frame(dims_frame, bg=Theme.CARD)
        inner_size_frame.grid(row=1, column=1, sticky="w", padx=10, pady=4)

        # Largura Interna
        self.inner_w_var = tk.StringVar(value="650")
        self.inner_w_entry = tk.Entry(
            inner_size_frame, textvariable=self.inner_w_var, width=6,
            font=Theme.FONT_MAIN, bg=Theme.SURFACE, fg=Theme.TEXT,
            insertbackground=Theme.TEXT, relief="flat",
            validate="key", validatecommand=vcmd,
            highlightthickness=1, highlightbackground="#2c2f3f",
            highlightcolor=Theme.ACCENT
        )
        self.inner_w_entry.pack(side="left")

        self.inner_w_auto = tk.BooleanVar(value=False)
        self.inner_w_cb = tk.Checkbutton(
            inner_size_frame, text="AUTO", variable=self.inner_w_auto,
            font=Theme.FONT_LABEL, bg=Theme.SURFACE, fg=Theme.MUTED,
            selectcolor=Theme.ACCENT, activebackground=Theme.ACCENT_HOV,
            activeforeground="#ffffff", relief="flat", cursor="hand2",
            indicatoron=False, padx=8, pady=3, bd=0,
            command=self._toggle_inner_w
        )
        self.inner_w_cb.pack(side="left", padx=(4, 10))

        tk.Label(
            inner_size_frame, text="x", font=Theme.FONT_BOLD,
            bg=Theme.CARD, fg=Theme.ACCENT
        ).pack(side="left", padx=2)

        # Altura Interna
        self.inner_h_var = tk.StringVar(value="AUTO")
        self.inner_h_entry = tk.Entry(
            inner_size_frame, textvariable=self.inner_h_var, width=6,
            font=Theme.FONT_MAIN, bg=Theme.SURFACE, fg=Theme.TEXT,
            insertbackground=Theme.TEXT, relief="flat",
            validate="key", validatecommand=vcmd, state="disabled",
            highlightthickness=1, highlightbackground="#2c2f3f",
            highlightcolor=Theme.ACCENT
        )
        self.inner_h_entry.pack(side="left")

        self.inner_h_auto = tk.BooleanVar(value=True)
        self.inner_h_cb = tk.Checkbutton(
            inner_size_frame, text="AUTO", variable=self.inner_h_auto,
            font=Theme.FONT_LABEL, bg=Theme.SURFACE, fg=Theme.MUTED,
            selectcolor=Theme.ACCENT, activebackground=Theme.ACCENT_HOV,
            activeforeground="#ffffff", relief="flat", cursor="hand2",
            indicatoron=False, padx=8, pady=3, bd=0,
            command=self._toggle_inner_h
        )
        self.inner_h_cb.pack(side="left", padx=(4, 4))
        tk.Label(inner_size_frame, text="px", font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED).pack(side="left", padx=4)

        # 3. Cor de Fundo do Canvas e Sufixo
        tk.Label(
            dims_frame, text="Cor de Fundo / Sufixo:",
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
        ).grid(row=2, column=0, sticky="w", pady=6)

        bg_suffix_frame = tk.Frame(dims_frame, bg=Theme.CARD)
        bg_suffix_frame.grid(row=2, column=1, sticky="w", padx=10, pady=6)

        self.bg_color_var = tk.StringVar(value="Transparente")
        self.bg_color_combo = ttk.Combobox(
            bg_suffix_frame, textvariable=self.bg_color_var,
            values=list(self.BG_COLORS.keys()), width=16, state="readonly"
        )
        self.bg_color_combo.pack(side="left", padx=(0, 10))

        tk.Label(bg_suffix_frame, text="Sufixo:", font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED).pack(side="left", padx=(4, 4))
        self.suffix_var = tk.StringVar(value="-fracta")
        self.suffix_entry = tk.Entry(
            bg_suffix_frame, textvariable=self.suffix_var, width=10,
            font=Theme.FONT_MAIN, bg=Theme.SURFACE, fg=Theme.TEXT,
            insertbackground=Theme.TEXT, relief="flat",
            highlightthickness=1, highlightbackground="#2c2f3f",
            highlightcolor=Theme.ACCENT
        )
        self.suffix_entry.pack(side="left")


        tk.Label(
            self.container, 
            text="* Nota: O ajuste funciona melhor com fundos lisos sólidos (como chromakey).",
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
        ).pack(anchor="w", pady=(2, 4))

        # Texto reativo de Preview Dinâmico
        self.preview_label = tk.Label(
            self.container, text="", font=Theme.FONT_LABEL,
            bg=Theme.CARD, fg=Theme.MUTED
        )
        self.preview_label.pack(anchor="w", pady=(0, 10))

        # Botão de Ação
        self.action_frame = tk.Frame(self.container, bg=Theme.CARD)
        self.action_frame.pack(fill="x")

        self.run_btn = tk.Button(
            self.action_frame,
            text="Ajustar Canvas",
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

        # Traces para atualização do preview
        self.canvas_w_var.trace_add("write", lambda *_: self._update_preview())
        self.canvas_h_var.trace_add("write", lambda *_: self._update_preview())
        self.bg_color_var.trace_add("write", lambda *_: self._update_preview())
        self.inner_w_var.trace_add("write", lambda *_: self._update_preview())
        self.inner_h_var.trace_add("write", lambda *_: self._update_preview())
        self._update_preview()


    def _update_input_mode(self) -> None:
        """Altera a interface com base no modo selecionado (lote ou unitario)."""
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

    def _toggle_inner_w(self) -> None:
        if self.inner_w_auto.get():
            self.inner_w_entry.config(state="disabled")
            self.inner_w_var.set("AUTO")
        else:
            self.inner_w_entry.config(state="normal")
            self.inner_w_var.set("650")
        self._update_preview()

    def _toggle_inner_h(self) -> None:
        if self.inner_h_auto.get():
            self.inner_h_entry.config(state="disabled")
            self.inner_h_var.set("AUTO")
        else:
            self.inner_h_entry.config(state="normal")
            self.inner_h_var.set("650")
        self._update_preview()

    def _update_preview(self) -> None:
        """Atualiza o resumo textual em tempo real de acordo com os parametros de Canvas."""
        try:
            w = self.canvas_w_var.get() or "0"
            h = self.canvas_h_var.get() or "0"
            bg = self.bg_color_var.get()
            
            # Limite interno
            if self.inner_w_auto.get() and self.inner_h_auto.get():
                inner_str = "tamanho proporcional automático"
            else:
                iw = "AUTO" if self.inner_w_auto.get() else f"{self.inner_w_var.get()}px"
                ih = "AUTO" if self.inner_h_auto.get() else f"{self.inner_h_var.get()}px"
                inner_str = f"limite máximo de {iw}x{ih}"
                
            self.preview_label.config(
                text=f"-> Moldura final: {w}x{h}px | Fundo: {bg} | Conteúdo: {inner_str}.",
                fg=Theme.SUCCESS
            )
        except Exception:
            self.preview_label.config(text="", fg=Theme.MUTED)


    def _start_processing(self) -> None:
        """Inicia o processamento assincrono do Canvas Fitter."""
        mode = self.mode_var.get()
        output_dir = self.output_row.get()

        if not output_dir:
            messagebox.showwarning("Atenção", "Selecione a pasta de saída.")
            return

        # Define caminho e tipo de entrada
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

        # Leitura das dimensoes
        try:
            canvas_w = int(self.canvas_w_var.get())
            canvas_h = int(self.canvas_h_var.get())
            if canvas_w <= 0 or canvas_h <= 0: raise ValueError
        except ValueError:
            messagebox.showwarning("Atenção", "Informe valores válidos maiores que 0 para o Canvas Externo.")
            return

        inner_w = None
        if not self.inner_w_auto.get():
            try:
                inner_w = int(self.inner_w_var.get())
                if inner_w <= 0: raise ValueError
            except ValueError:
                messagebox.showwarning("Atenção", "Informe largura limite numérica válida maior que 0.")
                return

        inner_h = None
        if not self.inner_h_auto.get():
            try:
                inner_h = int(self.inner_h_var.get())
                if inner_h <= 0: raise ValueError
            except ValueError:
                messagebox.showwarning("Atenção", "Informe altura limite numérica válida maior que 0.")
                return

        color_name = self.bg_color_var.get()
        bg_color = self.BG_COLORS.get(color_name, (0, 0, 0, 0))
        suffix_pattern = self.suffix_var.get().strip()

        # Desativa a interface gráfica durante processamento
        self.run_btn.config(state="disabled", text="Processando...")
        self.progress_bar.reset()
        self.log_panel.clear()

        def log_handler(msg):
            self.after(0, lambda m=msg: self.log_panel.write_log(m))

        def completion_handler(success):
            def _ui_update():
                self.run_btn.config(state="normal", text="Ajustar Canvas")
                self.progress_bar.set_progress(100)
                if success:
                    messagebox.showinfo("Concluído", "Ajuste de Canvas concluído com sucesso!")
            self.after(0, _ui_update)

        # Instancia o processador orientado a objetos
        fitter = CanvasFitter(
            canvas_w=canvas_w,
            canvas_h=canvas_h,
            inner_w=inner_w,
            inner_h=inner_h,
            bg_color=bg_color,
            suffix_pattern=suffix_pattern,
            log_fn=log_handler,
            progress_fn=self.progress_bar.set_progress,
            done_fn=completion_handler
        )

        target_fn = getattr(fitter, target_method)

        # Dispara thread
        thread = threading.Thread(
            target=target_fn,
            args=(input_path, output_dir),
            daemon=True
        )
        thread.start()
