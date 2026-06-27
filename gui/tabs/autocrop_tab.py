import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import threading
from gui.theme import Theme
from gui.widgets.folder_row import FolderRow
from gui.widgets.file_row import FileRow
from core.image_autocropper import ImageAutocropper

class AutocropTab(tk.Frame):
    """
    Aba que implementa a interface e controle para a funcionalidade de Aparar Bordas (Autocrop).
    Detecta e remove margens de cor solida ou transparentes ao redor da imagem.
    """
    def __init__(self, parent, log_panel, progress_bar):
        super().__init__(parent, bg=Theme.CARD)
        self.log_panel = log_panel
        self.progress_bar = progress_bar

        # Container interno para aplicacao do padding
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

        # Define layout inicial com base no modo padrao (pasta)
        self._update_input_mode()

        # 4. Painel de Configuracoes de Corte/Aparamento
        config_frame = tk.LabelFrame(
            self.container, text=" Configurações do Corte ",
            font=Theme.FONT_BOLD, bg=Theme.CARD, fg=Theme.ACCENT,
            bd=1, relief="solid", padx=12, pady=10
        )
        config_frame.pack(fill="x", pady=10)

        # Seletor de Tipo de Fundo a Aparar
        tk.Label(
            config_frame, text="Fundo a aparar:",
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
        ).grid(row=0, column=0, sticky="w", pady=6)

        self.trim_mode_var = tk.StringVar(value="auto")
        trim_modes_frame = tk.Frame(config_frame, bg=Theme.CARD)
        trim_modes_frame.grid(row=0, column=1, sticky="w", padx=10, pady=6)

        self.radio_auto = tk.Radiobutton(
            trim_modes_frame, text="Detectar Automático (Pixel 0,0)", variable=self.trim_mode_var,
            value="auto", font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.TEXT,
            selectcolor=Theme.SURFACE, activebackground=Theme.CARD,
            activeforeground=Theme.TEXT, command=self._update_trim_mode_ui
        )
        self.radio_auto.pack(side="left", padx=(0, 10))

        self.radio_trans = tk.Radiobutton(
            trim_modes_frame, text="Apenas Transparência", variable=self.trim_mode_var,
            value="transparency", font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.TEXT,
            selectcolor=Theme.SURFACE, activebackground=Theme.CARD,
            activeforeground=Theme.TEXT, command=self._update_trim_mode_ui
        )
        self.radio_trans.pack(side="left", padx=10)

        self.radio_color = tk.Radiobutton(
            trim_modes_frame, text="Cor Sólida Específica", variable=self.trim_mode_var,
            value="color", font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.TEXT,
            selectcolor=Theme.SURFACE, activebackground=Theme.CARD,
            activeforeground=Theme.TEXT, command=self._update_trim_mode_ui
        )
        self.radio_color.pack(side="left", padx=10)

        # Entrada de cor customizada (visivel apenas se modo for 'color')
        self.color_input_frame = tk.Frame(config_frame, bg=Theme.CARD)
        
        self.color_var = tk.StringVar(value="#ffffff")
        self.color_entry = tk.Entry(
            self.color_input_frame, textvariable=self.color_var, width=8,
            font=Theme.FONT_MAIN, bg=Theme.SURFACE, fg=Theme.TEXT,
            insertbackground=Theme.TEXT, relief="flat"
        )
        self.color_entry.pack(side="left", padx=(0, 6))
        self.color_var.trace_add("write", self._on_color_hex_changed)

        self.color_preview = tk.Frame(self.color_input_frame, width=20, height=20, bg="#ffffff", bd=1, relief="solid")
        self.color_preview.pack(side="left")
        
        # Slider de Tolerancia
        tk.Label(
            config_frame, text="Tolerância (0-255):",
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
        ).grid(row=2, column=0, sticky="w", pady=6)

        tolerance_frame = tk.Frame(config_frame, bg=Theme.CARD)
        tolerance_frame.grid(row=2, column=1, sticky="w", padx=10, pady=6)

        self.tolerance_var = tk.IntVar(value=10)
        self.tolerance_scale = tk.Scale(
            tolerance_frame, from_=0, to=255, orient="horizontal",
            variable=self.tolerance_var, showvalue=False,
            bg=Theme.CARD, fg=Theme.TEXT, activebackground=Theme.ACCENT,
            highlightbackground=Theme.CARD, highlightthickness=0,
            troughcolor=Theme.SURFACE, width=12, length=180, cursor="hand2"
        )
        self.tolerance_scale.pack(side="left", padx=(0, 8))

        self.tolerance_label = tk.Label(
            tolerance_frame, text="10", font=Theme.FONT_BOLD,
            bg=Theme.CARD, fg=Theme.ACCENT, width=3
        )
        self.tolerance_label.pack(side="left")
        self.tolerance_var.trace_add("write", lambda *_: self.tolerance_label.config(text=str(self.tolerance_var.get())))

        # Slider de Compressão PNG
        tk.Label(
            config_frame, text="Compressão PNG (0-9):",
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
        ).grid(row=3, column=0, sticky="w", pady=6)

        compress_frame = tk.Frame(config_frame, bg=Theme.CARD)
        compress_frame.grid(row=3, column=1, sticky="w", padx=10, pady=6)

        self.compress_var = tk.IntVar(value=6)
        self.compress_scale = tk.Scale(
            compress_frame, from_=0, to=9, orient="horizontal",
            variable=self.compress_var, showvalue=False,
            bg=Theme.CARD, fg=Theme.TEXT, activebackground=Theme.ACCENT,
            highlightbackground=Theme.CARD, highlightthickness=0,
            troughcolor=Theme.SURFACE, width=12, length=180, cursor="hand2"
        )
        self.compress_scale.pack(side="left", padx=(0, 8))

        self.compress_label = tk.Label(
            compress_frame, text="6", font=Theme.FONT_BOLD,
            bg=Theme.CARD, fg=Theme.ACCENT, width=3
        )
        self.compress_label.pack(side="left")
        self.compress_var.trace_add("write", lambda *_: self.compress_label.config(text=str(self.compress_var.get())))

        # Campo de Sufixo de Saida
        tk.Label(
            config_frame, text="Sufixo de Saída:",
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
        ).grid(row=4, column=0, sticky="w", pady=6)

        suffix_frame = tk.Frame(config_frame, bg=Theme.CARD)
        suffix_frame.grid(row=4, column=1, sticky="w", padx=10, pady=6)

        self.suffix_var = tk.StringVar(value="-cropped")
        self.suffix_entry = tk.Entry(
            suffix_frame, textvariable=self.suffix_var, width=12,
            font=Theme.FONT_MAIN, bg=Theme.SURFACE, fg=Theme.TEXT,
            insertbackground=Theme.TEXT, relief="flat"
        )
        self.suffix_entry.pack(side="left")

        # Mensagem informativa abaixo das configuracoes
        self.info_label = tk.Label(
            self.container, text="-> Remove as margens vazias ao redor de imagens, diminuindo a largura e altura do canvas.",
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
        )
        self.info_label.pack(anchor="w", pady=(8, 14))

        # Atualiza a exibicao inicial dos elementos condicionais da UI
        self._update_trim_mode_ui()

        # 5. Botao de Executar
        self.action_frame = tk.Frame(self.container, bg=Theme.CARD)
        self.action_frame.pack(fill="x")

        self.run_btn = tk.Button(
            self.action_frame,
            text="Aparar Bordas da Imagem",
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
        """Altera a visibilidade dos seletores dependendo se e lote ou imagem unica."""
        self.input_folder_row.pack_forget()
        self.input_file_row.pack_forget()
        self.output_row.pack_forget()

        if self.mode_var.get() == "folder":
            self.input_folder_row.pack(fill="x", pady=6)
        else:
            self.input_file_row.pack(fill="x", pady=6)

        self.output_row.pack(fill="x", pady=6)

    def _on_folder_input_changed(self, *args) -> None:
        """Define automaticamente uma pasta de saida sugerida ao mudar a entrada."""
        in_dir = self.input_folder_row.get()
        if in_dir and not self.output_row.get():
            self.output_row.set(str(Path(in_dir) / "output"))

    def _on_file_input_changed(self, *args) -> None:
        """Define automaticamente uma pasta de saida sugerida ao mudar o arquivo."""
        in_file = self.input_file_row.get()
        if in_file and not self.output_row.get():
            self.output_row.set(str(Path(in_file).parent / "output"))

    def _update_trim_mode_ui(self) -> None:
        """Mostra ou oculta o painel de cor customizada."""
        if self.trim_mode_var.get() == "color":
            self.color_input_frame.grid(row=1, column=1, sticky="w", padx=10, pady=2)
        else:
            self.color_input_frame.grid_forget()

    def _on_color_hex_changed(self, *args) -> None:
        """Valida e atualiza a cor do quadrado de preview quando o hex e alterado."""
        hex_val = self.color_var.get().strip()
        if hex_val.startswith("#") and len(hex_val) in (4, 7):
            try:
                self.color_preview.config(bg=hex_val)
            except Exception:
                pass
        elif len(hex_val) in (3, 6):
            try:
                self.color_preview.config(bg=f"#{hex_val}")
            except Exception:
                pass

    def _start_processing(self) -> None:
        """Inicia o processamento assincrono do autocrop em uma thread secundaria."""
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

        trim_mode = self.trim_mode_var.get()
        custom_color_hex = self.color_var.get().strip()
        
        # Valida formato hexadecimal se o modo for cor especifica
        if trim_mode == "color":
            if not custom_color_hex.startswith("#"):
                custom_color_hex = f"#{custom_color_hex}"
            if len(custom_color_hex) not in (4, 7):
                messagebox.showwarning("Atenção", "Informe um código de cor hexadecimal válido (Ex: #ffffff).")
                return

        tolerance = self.tolerance_var.get()
        suffix_pattern = self.suffix_var.get().strip()
        png_compress_level = self.compress_var.get()

        # Desativa o botao durante a execucao e limpa paineis globais
        self.run_btn.config(state="disabled", text="Processando...")
        self.progress_bar.reset()
        self.log_panel.clear()

        # Funcoes de manipulacao de logs e conclusao
        def log_handler(msg):
            self.after(0, lambda m=msg: self.log_panel.write_log(m))

        def completion_handler(success):
            def _ui_update():
                self.run_btn.config(state="normal", text="Aparar Bordas da Imagem")
                self.progress_bar.set_progress(100)
                if success:
                    messagebox.showinfo("Concluído", "Corte/Aparamento concluído com sucesso!")
            self.after(0, _ui_update)

        # Instancia o processador ImageAutocropper
        cropper = ImageAutocropper(
            trim_mode=trim_mode,
            custom_color_hex=custom_color_hex,
            tolerance=tolerance,
            suffix_pattern=suffix_pattern,
            png_compress_level=png_compress_level,
            log_fn=log_handler,
            progress_fn=self.progress_bar.set_progress,
            done_fn=completion_handler
        )

        target_fn = getattr(cropper, target_method)

        # Executa na thread secundaria para evitar travamento da GUI
        thread = threading.Thread(
            target=target_fn,
            args=(input_path, output_dir),
            daemon=True
        )
        thread.start()
