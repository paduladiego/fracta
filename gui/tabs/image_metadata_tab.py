import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import threading
from gui.theme import Theme
from gui.widgets.folder_row import FolderRow
from gui.widgets.file_row import FileRow
from core.metadata_processor import MetadataProcessor

class ImageMetadataTab(tk.Frame):
    """
    Interface para edicao de metadados EXIF em imagens (em lote ou unitario).
    """
    def __init__(self, parent, log_panel, progress_bar):
        super().__init__(parent, bg=Theme.CARD)
        self.log_panel = log_panel
        self.progress_bar = progress_bar

        # Container principal
        self.container = tk.Frame(self, bg=Theme.CARD)
        self.container.pack(fill="both", expand=True, padx=20, pady=16)

        # 1. Seletor de Modo de Entrada
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

        # 2. Frame de caminhos posicionado no topo
        self.paths_frame = tk.Frame(self.container, bg=Theme.CARD)
        self.paths_frame.pack(fill="x", pady=(0, 10))

        # Instancia seletores de entrada sob o paths_frame
        self.input_folder_row = FolderRow(
            self.paths_frame, 
            label_text="Pasta de entrada:", 
            dialog_title="Selecionar Pasta com Imagens"
        )
        self.input_folder_row.var.trace_add("write", self._on_folder_input_changed)

        self.input_file_row = FileRow(
            self.paths_frame, 
            label_text="Imagem de entrada:", 
            dialog_title="Selecionar Imagem"
        )
        self.input_file_row.var.trace_add("write", self._on_file_input_changed)
        self.input_file_row.var.trace_add("write", self._on_file_selected_for_read)

        # 3. Selecao de pasta de saida sob o paths_frame
        self.output_row = FolderRow(
            self.paths_frame, 
            label_text="Pasta de saída:", 
            dialog_title="Selecionar Pasta de Saída"
        )

        # Frame horizontal para dividir o editor (esquerda) e a leitura completa do EXIF (direita)
        self.layout_frame = tk.Frame(self.container, bg=Theme.CARD)
        self.layout_frame.pack(fill="both", expand=True, pady=(10, 0))

        # Coluna esquerda (Editor de Metadados)
        self.edit_col = tk.Frame(self.layout_frame, bg=Theme.CARD)
        self.edit_col.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Coluna direita (Informacoes Tecnicas Exif roláveis)
        self.info_col = tk.LabelFrame(
            self.layout_frame, text=" Metadados Detalhados (Leitura Exif) ",
            font=Theme.FONT_BOLD, bg=Theme.CARD, fg=Theme.ACCENT,
            bd=1, relief="solid", padx=12, pady=10
        )
        self.info_col.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # Caixa de texto rolável para exibir todos os metadados EXIF
        self.exif_text = tk.Text(
            self.info_col, wrap="word", font=("Consolas", 9),
            bg=Theme.SURFACE, fg="#dcdcdc", insertbackground=Theme.TEXT,
            relief="flat", bd=0, highlightthickness=0
        )
        self.exif_text.pack(fill="both", expand=True, side="left")

        # Scrollbar para o texto
        scrollbar = tk.Scrollbar(self.info_col, command=self.exif_text.yview, bg=Theme.CARD)
        scrollbar.pack(side="right", fill="y")
        self.exif_text.config(yscrollcommand=scrollbar.set)
        self.exif_text.config(state="disabled")

        # 4. Formulario de Metadados dentro do edit_col
        self.config_frame = tk.LabelFrame(
            self.edit_col, text=" Editor de Metadados EXIF (Imagem) ",
            font=Theme.FONT_BOLD, bg=Theme.CARD, fg=Theme.ACCENT,
            bd=1, relief="solid", padx=12, pady=10
        )
        self.config_frame.pack(fill="x", pady=10)

        # Campos StringVars
        self.artist_var = tk.StringVar()
        self.copyright_var = tk.StringVar()
        self.title_var = tk.StringVar()
        self.software_var = tk.StringVar()
        self.date_var = tk.StringVar()
        self.camera_var = tk.StringVar()
        self.strip_var = tk.BooleanVar(value=False)

        # Configura as caixas de texto com grid
        fields = [
            ("Artista / Autor:", self.artist_var, "normal"),
            ("Copyright:", self.copyright_var, "normal"),
            ("Título / Descrição:", self.title_var, "normal"),
            ("Software Editor:", self.software_var, "normal"),
            ("Data de Captura:", self.date_var, "normal"),
            ("Câmera / Equipamento:", self.camera_var, "readonly")
        ]

        self.entries = []
        for idx, (label_txt, s_var, entry_state) in enumerate(fields):
            tk.Label(
                self.config_frame, text=label_txt,
                font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
            ).grid(row=idx, column=0, sticky="w", pady=4)

            entry = tk.Entry(
                self.config_frame, textvariable=s_var, font=Theme.FONT_MAIN,
                bg=Theme.SURFACE, fg=Theme.TEXT if entry_state == "normal" else Theme.MUTED,
                insertbackground=Theme.TEXT, relief="flat", width=42,
                highlightthickness=1, highlightbackground="#2c2f3f",
                highlightcolor=Theme.ACCENT, state=entry_state
            )
            entry.grid(row=idx, column=1, sticky="w", padx=10, pady=4)
            self.entries.append(entry)

        # Checkbox de limpeza total de metadados
        self.cb_strip = tk.Checkbutton(
            self.config_frame, text="Remover todos os metadados (Limpeza de GPS e Privacidade)",
            variable=self.strip_var, font=Theme.FONT_LABEL, bg=Theme.SURFACE, fg=Theme.MUTED,
            selectcolor=Theme.ACCENT, activebackground=Theme.ACCENT_HOV,
            activeforeground="#ffffff", relief="flat", cursor="hand2",
            indicatoron=False, padx=12, pady=6, bd=0, command=self._toggle_strip_mode
        )
        self.cb_strip.grid(row=len(fields), column=0, columnspan=2, sticky="w", pady=10, padx=10)

        # 5. Botao de Acao dentro do edit_col
        self.action_frame = tk.Frame(self.edit_col, bg=Theme.CARD)
        self.action_frame.pack(fill="x", pady=(10, 0))

        self.run_btn = tk.Button(
            self.action_frame,
            text="Salvar Metadados",
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

        # Define layout inicial (chamado apos a criacao do run_btn)
        self._update_input_mode()

    def _toggle_strip_mode(self) -> None:
        """Desativa os campos de entrada caso a limpeza total esteja ativa."""
        state = "disabled" if self.strip_var.get() else "normal"
        self.cb_strip.config(bg=Theme.ACCENT if self.strip_var.get() else Theme.SURFACE, fg="#ffffff" if self.strip_var.get() else Theme.MUTED)
        
        for idx, entry in enumerate(self.entries):
            # O campo de camera sempre deve continuar desativado (readonly)
            if idx == 5:
                continue
            entry.config(state=state)

    def _update_input_mode(self) -> None:
        """Altera o layout visual baseado na selecao Lote vs Unitario."""
        self.input_folder_row.pack_forget()
        self.input_file_row.pack_forget()
        self.output_row.pack_forget()

        if self.mode_var.get() == "folder":
            self.input_folder_row.pack(fill="x", pady=6)
            self.run_btn.config(text="Salvar em Lote")
        else:
            self.input_file_row.pack(fill="x", pady=6)
            self.run_btn.config(text="Salvar Metadados")

        self.output_row.pack(fill="x", pady=6)

    def _on_folder_input_changed(self, *args) -> None:
        in_dir = self.input_folder_row.get()
        if in_dir and not self.output_row.get():
            self.output_row.set(str(Path(in_dir) / "output"))

    def _on_file_input_changed(self, *args) -> None:
        in_file = self.input_file_row.get()
        if in_file and not self.output_row.get():
            self.output_row.set(str(Path(in_file).parent / "output"))

    def _on_file_selected_for_read(self, *args) -> None:
        """Dispara a leitura assincrona das tags do arquivo unitario selecionado."""
        if self.mode_var.get() != "file":
            return
        
        file_path = self.input_file_row.get()
        if file_path and Path(file_path).is_file():
            def read_task():
                processor = MetadataProcessor(lambda _: None, lambda _: None, lambda _: None)
                meta = processor.read_image_metadata(Path(file_path))
                
                # Preenche caixas na thread principal
                self.after(0, lambda: self._fill_fields(meta))
            
            threading.Thread(target=read_task, daemon=True).start()

    def _fill_fields(self, metadata: dict) -> None:
        """Preenche o formulario com as tags EXIF obtidas."""
        self.artist_var.set(metadata.get("artist", ""))
        self.copyright_var.set(metadata.get("copyright", ""))
        self.title_var.set(metadata.get("title", ""))
        self.software_var.set(metadata.get("software", ""))
        self.date_var.set(metadata.get("datetime", ""))
        self.camera_var.set(metadata.get("camera", ""))
        
        # Preenche a listagem detalhada de todas as tags Exif
        self.exif_text.config(state="normal")
        self.exif_text.delete("1.0", tk.END)
        
        all_exif = metadata.get("all_exif", {})
        if all_exif:
            lines = []
            for k, v in sorted(all_exif.items()):
                # Ignora valores de bytes muito longos (ex: dados binarios raw)
                if isinstance(v, (bytes, bytearray)) and len(v) > 200:
                    v = f"<Dados binários: {len(v)} bytes>"
                lines.append(f"{k}: {v}")
            self.exif_text.insert("1.0", "\n".join(lines))
        else:
            self.exif_text.insert("1.0", "Nenhum metadado EXIF detalhado encontrado neste arquivo.")
            
        self.exif_text.config(state="disabled")

    def _start_processing(self) -> None:
        """Inicia a gravacao assincrona dos metadados."""
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
            target_method = "process_image_batch"
        else:
            input_path = self.input_file_row.get()
            if not input_path:
                messagebox.showwarning("Atenção", "Selecione o arquivo de imagem.")
                return
            target_method = "process_image_single"

        # Coleta dados do formulario
        meta = {
            "artist": self.artist_var.get().strip(),
            "copyright": self.copyright_var.get().strip(),
            "title": self.title_var.get().strip(),
            "software": self.software_var.get().strip(),
            "datetime": self.date_var.get().strip()
        }
        strip_all = self.strip_var.get()

        # Desativa a UI
        self.run_btn.config(state="disabled", text="Processando...")
        self.progress_bar.reset()
        self.log_panel.clear()

        def log_handler(msg):
            self.after(0, lambda m=msg: self.log_panel.write_log(m))

        def completion_handler(success):
            def _ui_update():
                self.run_btn.config(state="normal", text="Salvar em Lote" if mode == "folder" else "Salvar Metadados")
                self.progress_bar.set_progress(100)
                if success:
                    messagebox.showinfo("Concluído", "Edição de metadados da imagem concluída com sucesso!")
            self.after(0, _ui_update)

        processor = MetadataProcessor(
            log_fn=log_handler,
            progress_fn=self.progress_bar.set_progress,
            done_fn=completion_handler
        )

        target_fn = getattr(processor, target_method)

        # Thread de segundo plano
        thread = threading.Thread(
            target=target_fn,
            args=(input_path, output_dir, meta, strip_all),
            daemon=True
        )
        thread.start()
