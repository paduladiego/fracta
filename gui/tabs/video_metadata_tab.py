import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import threading
from gui.theme import Theme
from gui.widgets.folder_row import FolderRow
from gui.widgets.file_row import FileRow
from core.metadata_processor import MetadataProcessor
from core.constants import SUPPORTED_VIDEO_EXTENSIONS

class VideoMetadataTab(tk.Frame):
    """
    Interface para edicao de metadados de video (em lote ou unitario) usando FFmpeg.
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
            self.mode_frame, text="Vídeo Único", variable=self.mode_var,
            value="file", font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.TEXT,
            selectcolor=Theme.SURFACE, activebackground=Theme.CARD,
            activeforeground=Theme.TEXT, command=self._update_input_mode
        )
        self.radio_file.pack(side="left", padx=10)

        # 2. Instancia seletores de entrada
        self.input_folder_row = FolderRow(
            self.container, 
            label_text="Pasta de entrada:", 
            dialog_title="Selecionar Pasta com Vídeos"
        )
        self.input_folder_row.var.trace_add("write", self._on_folder_input_changed)

        self.input_file_row = FileRow(
            self.container, 
            label_text="Vídeo de entrada:", 
            dialog_title="Selecionar Vídeo",
            file_extensions=SUPPORTED_VIDEO_EXTENSIONS,
            filetypes_label="Vídeos Suportados"
        )
        self.input_file_row.var.trace_add("write", self._on_file_input_changed)
        self.input_file_row.var.trace_add("write", self._on_file_selected_for_read)

        # 3. Selecao de pasta de saida
        self.output_row = FolderRow(
            self.container, 
            label_text="Pasta de saída:", 
            dialog_title="Selecionar Pasta de Saída"
        )

        # 4. Formulario de Metadados
        self.config_frame = tk.LabelFrame(
            self.container, text=" Editor de Metadados de Vídeo ",
            font=Theme.FONT_BOLD, bg=Theme.CARD, fg=Theme.ACCENT,
            bd=1, relief="solid", padx=12, pady=10
        )
        self.config_frame.pack(fill="x", pady=10)

        # Campos StringVars
        self.artist_var = tk.StringVar()
        self.copyright_var = tk.StringVar()
        self.title_var = tk.StringVar()
        self.comment_var = tk.StringVar()
        self.strip_var = tk.BooleanVar(value=False)

        # Configura as caixas de texto com grid
        fields = [
            ("Artista / Autor:", self.artist_var),
            ("Copyright:", self.copyright_var),
            ("Título do Vídeo:", self.title_var),
            ("Comentários / Descrição:", self.comment_var)
        ]

        self.entries = []
        for idx, (label_txt, s_var) in enumerate(fields):
            tk.Label(
                self.config_frame, text=label_txt,
                font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
            ).grid(row=idx, column=0, sticky="w", pady=4)

            entry = tk.Entry(
                self.config_frame, textvariable=s_var, font=Theme.FONT_MAIN,
                bg=Theme.SURFACE, fg=Theme.TEXT,
                insertbackground=Theme.TEXT, relief="flat", width=42,
                highlightthickness=1, highlightbackground="#2c2f3f",
                highlightcolor=Theme.ACCENT
            )
            entry.grid(row=idx, column=1, sticky="w", padx=10, pady=4)
            self.entries.append(entry)

        # Checkbox de limpeza total de metadados
        self.cb_strip = tk.Checkbutton(
            self.config_frame, text="Remover todos os metadados do container de vídeo",
            variable=self.strip_var, font=Theme.FONT_LABEL, bg=Theme.SURFACE, fg=Theme.MUTED,
            selectcolor=Theme.ACCENT, activebackground=Theme.ACCENT_HOV,
            activeforeground="#ffffff", relief="flat", cursor="hand2",
            indicatoron=False, padx=12, pady=6, bd=0, command=self._toggle_strip_mode
        )
        self.cb_strip.grid(row=len(fields), column=0, columnspan=2, sticky="w", pady=10, padx=10)

        # 5. Botao de Acao
        self.action_frame = tk.Frame(self.container, bg=Theme.CARD)
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
        
        for entry in self.entries:
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
        """Dispara a leitura assincrona dos metadados do video selecionado."""
        if self.mode_var.get() != "file":
            return
        
        file_path = self.input_file_row.get()
        if file_path and Path(file_path).is_file():
            def read_task():
                processor = MetadataProcessor(lambda _: None, lambda _: None, lambda _: None)
                meta = processor.read_video_metadata(Path(file_path))
                
                # Preenche caixas na thread principal
                self.after(0, lambda: self._fill_fields(meta))
            
            threading.Thread(target=read_task, daemon=True).start()

    def _fill_fields(self, metadata: dict) -> None:
        """Preenche o formulario com os metadados do video obtidos."""
        self.artist_var.set(metadata.get("artist", ""))
        self.copyright_var.set(metadata.get("copyright", ""))
        self.title_var.set(metadata.get("title", ""))
        self.comment_var.set(metadata.get("comment", ""))

    def _start_processing(self) -> None:
        """Inicia a gravacao assincrona dos metadados de video via FFmpeg."""
        # Checa FFmpeg
        from core.video_processor import VideoProcessor
        if not VideoProcessor.check_ffmpeg():
            messagebox.showerror("Erro", "FFmpeg não encontrado no sistema. Por favor, configure o FFmpeg no PATH.")
            return

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
            target_method = "process_video_batch"
        else:
            input_path = self.input_file_row.get()
            if not input_path:
                messagebox.showwarning("Atenção", "Selecione o arquivo de vídeo.")
                return
            target_method = "process_video_single"

        # Coleta dados do formulario
        meta = {
            "artist": self.artist_var.get().strip(),
            "copyright": self.copyright_var.get().strip(),
            "title": self.title_var.get().strip(),
            "comment": self.comment_var.get().strip()
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
                    messagebox.showinfo("Concluído", "Edição de metadados de vídeo concluída com sucesso!")
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
