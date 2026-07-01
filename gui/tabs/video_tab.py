import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import threading
from gui.theme import Theme
from gui.widgets.folder_row import FolderRow
from gui.widgets.file_row import FileRow
from core.video_processor import VideoProcessor
from core.constants import SUPPORTED_VIDEO_EXTENSIONS

class VideoTab(tk.Frame):
    """
    Aba que implementa a interface e controle para a funcionalidade de Comprimir/Converter Vídeos.
    Permite otimizar videos para a web com H.264 (MP4) ou VP9 (WebM) usando o FFmpeg.
    """
    def __init__(self, parent, log_panel, progress_bar):
        super().__init__(parent, bg=Theme.CARD)
        self.log_panel = log_panel
        self.progress_bar = progress_bar
        self.processor = None

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
            self.mode_frame, text="Vídeo Único", variable=self.mode_var,
            value="file", font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.TEXT,
            selectcolor=Theme.SURFACE, activebackground=Theme.CARD,
            activeforeground=Theme.TEXT, command=self._update_input_mode
        )
        self.radio_file.pack(side="left", padx=10)

        # 2. Instancia seletores de entrada (pasta ou arquivo unico)
        self.input_folder_row = FolderRow(
            self.container, 
            label_text="Pasta de entrada:", 
            dialog_title="Selecionar Pasta com Vídeos"
        )
        self.input_folder_row.var.trace_add("write", self._on_folder_input_changed)

        self.input_file_row = FileRow(
            self.container, 
            label_text="Vídeo de entrada:", 
            dialog_title="Selecionar Arquivo de Vídeo",
            file_extensions=SUPPORTED_VIDEO_EXTENSIONS,
            filetypes_label="Vídeos Suportados"
        )
        self.input_file_row.var.trace_add("write", self._on_file_input_changed)

        # 3. Selecao de pasta de saida
        self.output_row = FolderRow(
            self.container, 
            label_text="Pasta de saída:", 
            dialog_title="Selecionar Pasta de Saída"
        )

        # Define layout inicial
        self._update_input_mode()

        # 4. Painel de Configuracoes de Video
        config_frame = tk.LabelFrame(
            self.container, text=" Configurações de Vídeo (Web) ",
            font=Theme.FONT_BOLD, bg=Theme.CARD, fg=Theme.ACCENT,
            bd=1, relief="solid", padx=12, pady=10
        )
        config_frame.pack(fill="x", pady=10)

        # Formato de Saida (MP4 vs WebM)
        tk.Label(
            config_frame, text="Formato de Saída:",
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
        ).grid(row=0, column=0, sticky="w", pady=6)

        self.format_var = tk.StringVar(value=".mp4")
        format_sel_frame = tk.Frame(config_frame, bg=Theme.CARD)
        format_sel_frame.grid(row=0, column=1, sticky="w", padx=10, pady=6)

        self.rb_mp4 = tk.Radiobutton(
            format_sel_frame, text="MP4 (H.264/AAC - Máxima Compatibilidade)", variable=self.format_var,
            value=".mp4", font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.TEXT,
            selectcolor=Theme.SURFACE, activebackground=Theme.CARD,
            activeforeground=Theme.TEXT
        )
        self.rb_mp4.pack(anchor="w")

        self.rb_webm = tk.Radiobutton(
            format_sel_frame, text="WebM (VP9/Opus - Alta Compressão Web)", variable=self.format_var,
            value=".webm", font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.TEXT,
            selectcolor=Theme.SURFACE, activebackground=Theme.CARD,
            activeforeground=Theme.TEXT
        )
        self.rb_webm.pack(anchor="w")

        # Resolucao de Saida
        tk.Label(
            config_frame, text="Resolução Alvo:",
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
        ).grid(row=1, column=0, sticky="w", pady=6)

        self.resolution_var = tk.StringVar(value="original")
        res_sel_frame = tk.Frame(config_frame, bg=Theme.CARD)
        res_sel_frame.grid(row=1, column=1, sticky="w", padx=10, pady=6)

        resolutions = [
            ("Original", "original"),
            ("1080p (Full HD)", "1080p"),
            ("720p (HD)", "720p"),
            ("480p (SD)", "480p")
        ]

        for text, val in resolutions:
            rb = tk.Radiobutton(
                res_sel_frame, text=text, variable=self.resolution_var,
                value=val, font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.TEXT,
                selectcolor=Theme.SURFACE, activebackground=Theme.CARD,
                activeforeground=Theme.TEXT
            )
            rb.pack(side="left", padx=(0, 10))

        # Qualidade de Saida
        tk.Label(
            config_frame, text="Qualidade / Peso:",
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
        ).grid(row=2, column=0, sticky="w", pady=6)

        self.quality_var = tk.StringVar(value="balanced")
        qual_sel_frame = tk.Frame(config_frame, bg=Theme.CARD)
        qual_sel_frame.grid(row=2, column=1, sticky="w", padx=10, pady=6)

        qualities = [
            ("Alta Qualidade", "high"),
            ("Balanceado", "balanced"),
            ("Tamanho Mínimo (Web)", "low")
        ]

        for text, val in qualities:
            rb = tk.Radiobutton(
                qual_sel_frame, text=text, variable=self.quality_var,
                value=val, font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.TEXT,
                selectcolor=Theme.SURFACE, activebackground=Theme.CARD,
                activeforeground=Theme.TEXT
            )
            rb.pack(side="left", padx=(0, 10))

        # Remocao de Audio
        tk.Label(
            config_frame, text="Ajustes Extras:",
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
        ).grid(row=3, column=0, sticky="w", pady=6)

        self.audio_var = tk.BooleanVar(value=False)
        self.cb_audio = tk.Checkbutton(
            config_frame, text="Remover Trilha de Áudio (Silenciar)", variable=self.audio_var,
            font=Theme.FONT_LABEL, bg=Theme.SURFACE, fg=Theme.MUTED,
            selectcolor=Theme.ACCENT, activebackground=Theme.ACCENT_HOV,
            activeforeground="#ffffff", relief="flat", cursor="hand2",
            indicatoron=False, padx=12, pady=6, bd=0
        )
        self.cb_audio.grid(row=3, column=1, sticky="w", padx=10, pady=6)

        # Traces para atualizacao visual de chip
        self.audio_var.trace_add("write", lambda *_: self._update_chip_style())
        self._update_chip_style()

        # Texto explicativo dinamico
        self.info_label = tk.Label(
            self.container, text="",
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
        )
        self.info_label.pack(anchor="w", pady=(8, 14))

        self.format_var.trace_add("write", lambda *_: self._update_preview())
        self.resolution_var.trace_add("write", lambda *_: self._update_preview())
        self.quality_var.trace_add("write", lambda *_: self._update_preview())
        self.audio_var.trace_add("write", lambda *_: self._update_preview())
        self._update_preview()

        # 5. Botao de Acao
        self.action_frame = tk.Frame(self.container, bg=Theme.CARD)
        self.action_frame.pack(fill="x")

        self.run_btn = tk.Button(
            self.action_frame,
            text="Comprimir Vídeos",
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

    def _update_chip_style(self) -> None:
        """Ajusta cor de fundo do checkbox de remover audio conforme selecao."""
        if self.audio_var.get():
            self.cb_audio.config(bg=Theme.ACCENT, fg="#ffffff")
        else:
            self.cb_audio.config(bg=Theme.SURFACE, fg=Theme.MUTED)

    def _update_input_mode(self) -> None:
        """Altera a interface com base no modo de entrada selecionado."""
        self.input_folder_row.pack_forget()
        self.input_file_row.pack_forget()
        self.output_row.pack_forget()

        if self.mode_var.get() == "folder":
            self.input_folder_row.pack(fill="x", pady=6)
        else:
            self.input_file_row.pack(fill="x", pady=6)

        self.output_row.pack(fill="x", pady=6)

    def _on_folder_input_changed(self, *args) -> None:
        """Sugere uma pasta de saida baseada na entrada."""
        in_dir = self.input_folder_row.get()
        if in_dir and not self.output_row.get():
            self.output_row.set(str(Path(in_dir) / "output"))

    def _on_file_input_changed(self, *args) -> None:
        """Sugere uma pasta de saida baseada no arquivo de entrada."""
        in_file = self.input_file_row.get()
        if in_file and not self.output_row.get():
            self.output_row.set(str(Path(in_file).parent / "output"))

    def _update_preview(self) -> None:
        """Atualiza a mensagem informativa em tempo real."""
        try:
            fmt = self.format_var.get()
            res = self.resolution_var.get()
            qual = self.quality_var.get()
            no_audio = self.audio_var.get()

            # Mapeia termos para exibicao
            res_str = "Resolução Original" if res == "original" else f"Reescala para {res}"
            qual_str = "Bitrate Baixo (Alta Compressão)" if qual == "low" else ("Bitrate Alto (Qualidade Máxima)" if qual == "high" else "Bitrate Médio (Balanceado)")
            audio_str = " | Sem Áudio (Mudo)" if no_audio else ""
            codec_str = "H.264/AAC" if fmt == ".mp4" else "VP9/Opus"

            msg = f"-> Destino: {codec_str} ({fmt}) | {res_str} | {qual_str}{audio_str}."
            self.info_label.config(text=msg, fg=Theme.SUCCESS)
        except Exception:
            self.info_label.config(text="", fg=Theme.MUTED)

    def _start_processing(self) -> None:
        """Dispara a compressao de videos em segundo plano."""
        # Checa presenca do FFmpeg primeiro
        if not VideoProcessor.check_ffmpeg():
            msg = (
                "FFmpeg não foi encontrado no sistema!\n\n"
                "Para processar vídeos, você precisa ter o FFmpeg instalado e configurado no PATH do Windows.\n\n"
                "Instruções:\n"
                "1. Baixe o FFmpeg (ffmpeg.org)\n"
                "2. Extraia e adicione a pasta 'bin' nas Variáveis de Ambiente do Sistema (PATH)."
            )
            messagebox.showerror("FFmpeg Ausente", msg)
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
            if not Path(input_path).is_dir():
                messagebox.showerror("Erro", f"Pasta de entrada não encontrada:\n{input_path}")
                return
            target_method = "process_batch"
        else:
            input_path = self.input_file_row.get()
            if not input_path:
                messagebox.showwarning("Atenção", "Selecione o vídeo de entrada.")
                return
            if not Path(input_path).is_file():
                messagebox.showerror("Erro", f"Vídeo de entrada não encontrado:\n{input_path}")
                return
            target_method = "process_single"

        format_ext = self.format_var.get()
        resolution = self.resolution_var.get()
        quality = self.quality_var.get()
        remove_audio = self.audio_var.get()

        # Desativa a UI e reinicia log/progresso
        self.run_btn.config(state="disabled", text="Processando Vídeo...")
        self.progress_bar.reset()
        self.log_panel.clear()

        def log_handler(msg):
            self.after(0, lambda m=msg: self.log_panel.write_log(m))

        def completion_handler(success):
            def _ui_update():
                self.run_btn.config(state="normal", text="Comprimir Vídeos")
                self.progress_bar.set_progress(100)
                if success:
                    messagebox.showinfo("Concluído", "Compressão de vídeo concluída com sucesso!")
            self.after(0, _ui_update)

        self.processor = VideoProcessor(
            log_fn=log_handler,
            progress_fn=self.progress_bar.set_progress,
            done_fn=completion_handler
        )

        target_fn = getattr(self.processor, target_method)

        # Inicia processamento assincrono
        thread = threading.Thread(
            target=target_fn,
            args=(input_path, output_dir, format_ext, resolution, quality, remove_audio),
            daemon=True
        )
        thread.start()
