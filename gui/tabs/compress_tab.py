import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import threading
from gui.theme import Theme
from gui.widgets.folder_row import FolderRow
from gui.widgets.file_row import FileRow
from core.image_compressor import ImageCompressor

class CompressTab(tk.Frame):
    """
    Aba que implementa a interface e controle para a funcionalidade de Comprimir Imagens.
    Permite reduzir o peso de arquivos PNG (0-9), JPEG (1-100) e WebP (1-100).
    """
    def __init__(self, parent, log_panel, progress_bar):
        super().__init__(parent, bg=Theme.CARD)
        self.log_panel = log_panel
        self.progress_bar = progress_bar

        # Container interno com margens de padding
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

        # 2. Instancia seletores de entrada (pasta ou arquivo unico)
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

        # 3. Selecao de pasta de saida
        self.output_row = FolderRow(
            self.container, 
            label_text="Pasta de saida:", 
            dialog_title="Selecionar Pasta de Saida"
        )

        # Define layout inicial
        self._update_input_mode()

        # 4. Painel de Configuracoes de Otimizacao
        config_frame = tk.LabelFrame(
            self.container, text=" Configurações de Otimização (Web) ",
            font=Theme.FONT_BOLD, bg=Theme.CARD, fg=Theme.ACCENT,
            bd=1, relief="solid", padx=12, pady=10
        )
        config_frame.pack(fill="x", pady=10)

        # Slider de Compressao PNG (0-9)
        tk.Label(
            config_frame, text="Compressão PNG (0-9):",
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
        ).grid(row=0, column=0, sticky="w", pady=6)

        png_frame = tk.Frame(config_frame, bg=Theme.CARD)
        png_frame.grid(row=0, column=1, sticky="w", padx=10, pady=6)

        self.png_var = tk.IntVar(value=6)
        self.png_scale = tk.Scale(
            png_frame, from_=0, to=9, orient="horizontal",
            variable=self.png_var, showvalue=False,
            bg=Theme.CARD, fg=Theme.TEXT, activebackground=Theme.ACCENT,
            highlightbackground=Theme.CARD, highlightthickness=0,
            troughcolor=Theme.SURFACE, width=12, length=180, cursor="hand2"
        )
        self.png_scale.pack(side="left", padx=(0, 8))

        self.png_label = tk.Label(
            png_frame, text="6", font=Theme.FONT_BOLD,
            bg=Theme.CARD, fg=Theme.ACCENT, width=3
        )
        self.png_label.pack(side="left")
        self.png_var.trace_add("write", lambda *_: self.png_label.config(text=str(self.png_var.get())))

        # Slider de Qualidade JPEG (1-100)
        tk.Label(
            config_frame, text="Qualidade JPEG (1-100):",
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
        ).grid(row=1, column=0, sticky="w", pady=6)

        jpeg_frame = tk.Frame(config_frame, bg=Theme.CARD)
        jpeg_frame.grid(row=1, column=1, sticky="w", padx=10, pady=6)

        self.jpeg_var = tk.IntVar(value=85)
        self.jpeg_scale = tk.Scale(
            jpeg_frame, from_=1, to=100, orient="horizontal",
            variable=self.jpeg_var, showvalue=False,
            bg=Theme.CARD, fg=Theme.TEXT, activebackground=Theme.ACCENT,
            highlightbackground=Theme.CARD, highlightthickness=0,
            troughcolor=Theme.SURFACE, width=12, length=180, cursor="hand2"
        )
        self.jpeg_scale.pack(side="left", padx=(0, 8))

        self.jpeg_label = tk.Label(
            jpeg_frame, text="85", font=Theme.FONT_BOLD,
            bg=Theme.CARD, fg=Theme.ACCENT, width=3
        )
        self.jpeg_label.pack(side="left")
        self.jpeg_var.trace_add("write", lambda *_: self.jpeg_label.config(text=str(self.jpeg_var.get())))

        # Slider de Qualidade WebP (1-100)
        tk.Label(
            config_frame, text="Qualidade WebP (1-100):",
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
        ).grid(row=2, column=0, sticky="w", pady=6)

        webp_frame = tk.Frame(config_frame, bg=Theme.CARD)
        webp_frame.grid(row=2, column=1, sticky="w", padx=10, pady=6)

        self.webp_var = tk.IntVar(value=85)
        self.webp_scale = tk.Scale(
            webp_frame, from_=1, to=100, orient="horizontal",
            variable=self.webp_var, showvalue=False,
            bg=Theme.CARD, fg=Theme.TEXT, activebackground=Theme.ACCENT,
            highlightbackground=Theme.CARD, highlightthickness=0,
            troughcolor=Theme.SURFACE, width=12, length=180, cursor="hand2"
        )
        self.webp_scale.pack(side="left", padx=(0, 8))

        self.webp_label = tk.Label(
            webp_frame, text="85", font=Theme.FONT_BOLD,
            bg=Theme.CARD, fg=Theme.ACCENT, width=3
        )
        self.webp_label.pack(side="left")
        self.webp_var.trace_add("write", lambda *_: self.webp_label.config(text=str(self.webp_var.get())))

        # Formatos de Exportação (Checkboxes para Múltiplas Saídas)
        tk.Label(
            config_frame, text="Converter/Exportar para:",
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
        ).grid(row=3, column=0, sticky="w", pady=6)

        format_frame = tk.Frame(config_frame, bg=Theme.CARD)
        format_frame.grid(row=3, column=1, sticky="w", padx=10, pady=6)

        self.fmt_orig_var = tk.BooleanVar(value=True)
        self.fmt_png_var = tk.BooleanVar(value=False)
        self.fmt_jpg_var = tk.BooleanVar(value=False)
        self.fmt_webp_var = tk.BooleanVar(value=False)

        self.cb_fmt_orig = tk.Checkbutton(
            format_frame, text="Manter Original", variable=self.fmt_orig_var,
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.TEXT,
            selectcolor=Theme.SURFACE, activebackground=Theme.CARD,
            activeforeground=Theme.TEXT
        )
        self.cb_fmt_orig.pack(side="left", padx=(0, 10))

        self.cb_fmt_png = tk.Checkbutton(
            format_frame, text="PNG", variable=self.fmt_png_var,
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.TEXT,
            selectcolor=Theme.SURFACE, activebackground=Theme.CARD,
            activeforeground=Theme.TEXT
        )
        self.cb_fmt_png.pack(side="left", padx=10)

        self.cb_fmt_jpg = tk.Checkbutton(
            format_frame, text="JPEG", variable=self.fmt_jpg_var,
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.TEXT,
            selectcolor=Theme.SURFACE, activebackground=Theme.CARD,
            activeforeground=Theme.TEXT
        )
        self.cb_fmt_jpg.pack(side="left", padx=10)

        self.cb_fmt_webp = tk.Checkbutton(
            format_frame, text="WebP", variable=self.fmt_webp_var,
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.TEXT,
            selectcolor=Theme.SURFACE, activebackground=Theme.CARD,
            activeforeground=Theme.TEXT
        )
        self.cb_fmt_webp.pack(side="left", padx=10)

        # Checkboxes de Otimização Adicionais (Metadados e SEO)
        tk.Label(
            config_frame, text="Otimizações Adicionais:",
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
        ).grid(row=4, column=0, sticky="w", pady=6)

        options_frame = tk.Frame(config_frame, bg=Theme.CARD)
        options_frame.grid(row=4, column=1, sticky="w", padx=10, pady=6)

        self.metadata_var = tk.BooleanVar(value=True)
        self.metadata_cb = tk.Checkbutton(
            options_frame, text="Remover Metadados (EXIF/ICC)", variable=self.metadata_var,
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.TEXT,
            selectcolor=Theme.SURFACE, activebackground=Theme.CARD,
            activeforeground=Theme.TEXT
        )
        self.metadata_cb.pack(side="left", padx=(0, 20))

        self.seo_var = tk.BooleanVar(value=True)
        self.seo_cb = tk.Checkbutton(
            options_frame, text="Nome de Arquivo Amigável (SEO)", variable=self.seo_var,
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.TEXT,
            selectcolor=Theme.SURFACE, activebackground=Theme.CARD,
            activeforeground=Theme.TEXT
        )
        self.seo_cb.pack(side="left", padx=10)

        # Campo de Sufixo de Saida
        tk.Label(
            config_frame, text="Sufixo de Saída:",
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
        ).grid(row=5, column=0, sticky="w", pady=6)

        suffix_frame = tk.Frame(config_frame, bg=Theme.CARD)
        suffix_frame.grid(row=5, column=1, sticky="w", padx=10, pady=6)

        self.suffix_var = tk.StringVar(value="-compressed")
        self.suffix_entry = tk.Entry(
            suffix_frame, textvariable=self.suffix_var, width=12,
            font=Theme.FONT_MAIN, bg=Theme.SURFACE, fg=Theme.TEXT,
            insertbackground=Theme.TEXT, relief="flat"
        )
        self.suffix_entry.pack(side="left")

        # Texto Informativo de Otimizacao
        self.info_label = tk.Label(
            self.container, text="-> Otimiza arquivos reduzindo o tamanho em disco, ideal para melhorar a performance de sites.",
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
        )
        self.info_label.pack(anchor="w", pady=(8, 14))

        # 5. Botao de Acao
        self.action_frame = tk.Frame(self.container, bg=Theme.CARD)
        self.action_frame.pack(fill="x")

        self.run_btn = tk.Button(
            self.action_frame,
            text="Comprimir Imagens",
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
        """Sugere automaticamente uma pasta de saida baseada na entrada."""
        in_dir = self.input_folder_row.get()
        if in_dir and not self.output_row.get():
            self.output_row.set(str(Path(in_dir) / "output"))

    def _on_file_input_changed(self, *args) -> None:
        """Sugere automaticamente uma pasta de saida baseada no arquivo de entrada."""
        in_file = self.input_file_row.get()
        if in_file and not self.output_row.get():
            self.output_row.set(str(Path(in_file).parent / "output"))

    def _start_processing(self) -> None:
        """Inicia a compressao das imagens de forma assincrona em thread secundaria."""
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

        png_compress_level = self.png_var.get()
        jpeg_quality = self.jpeg_var.get()
        webp_quality = self.webp_var.get()
        suffix_pattern = self.suffix_var.get().strip()
        
        # Recupera as novas configurações de SEO, Metadados e Formatos de Conversão
        export_original = self.fmt_orig_var.get()
        export_png = self.fmt_png_var.get()
        export_jpeg = self.fmt_jpg_var.get()
        export_webp = self.fmt_webp_var.get()
        
        # Validação para garantir que pelo menos um formato foi selecionado
        if not (export_original or export_png or export_jpeg or export_webp):
            messagebox.showwarning("Atenção", "Selecione pelo menos um formato de exportação (ex: Manter Original, PNG, JPEG ou WebP).")
            return
            
        strip_metadata = self.metadata_var.get()
        seo_friendly_names = self.seo_var.get()

        # Desativa a UI e limpa painel
        self.run_btn.config(state="disabled", text="Processando...")
        self.progress_bar.reset()
        self.log_panel.clear()

        def log_handler(msg):
            self.after(0, lambda m=msg: self.log_panel.write_log(m))

        def completion_handler(success):
            def _ui_update():
                self.run_btn.config(state="normal", text="Comprimir Imagens")
                self.progress_bar.set_progress(100)
                if success:
                    messagebox.showinfo("Concluído", "Compressão de imagens concluída com sucesso!")
            self.after(0, _ui_update)

        # Instancia o processador ImageCompressor passando os novos flags de exportacao
        compressor = ImageCompressor(
            png_compress_level=png_compress_level,
            jpeg_quality=jpeg_quality,
            webp_quality=webp_quality,
            suffix_pattern=suffix_pattern,
            export_original=export_original,
            export_png=export_png,
            export_jpeg=export_jpeg,
            export_webp=export_webp,
            strip_metadata=strip_metadata,
            seo_friendly_names=seo_friendly_names,
            log_fn=log_handler,
            progress_fn=self.progress_bar.set_progress,
            done_fn=completion_handler
        )

        target_fn = getattr(compressor, target_method)

        # Dispara thread
        thread = threading.Thread(
            target=target_fn,
            args=(input_path, output_dir),
            daemon=True
        )
        thread.start()
