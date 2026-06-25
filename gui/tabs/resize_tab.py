import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import threading
from gui.theme import Theme
from gui.widgets.folder_row import FolderRow
from core.image_resizer import process_resize_folder

class ResizeTab(tk.Frame):
    """
    Aba que implementa a interface e controle para a funcionalidade de Redimensionar Imagens.
    Permite redimensionar em lote fixando um dos eixos e mantendo a proporção original.
    """
    def __init__(self, parent, log_panel, progress_bar):
        super().__init__(parent, bg=Theme.CARD)
        self.log_panel = log_panel
        self.progress_bar = progress_bar

        # Container interno
        self.container = tk.Frame(self, bg=Theme.CARD)
        self.container.pack(fill="both", expand=True, padx=20, pady=16)

        # Seleção de pasta de entrada
        self.input_row = FolderRow(
            self.container, 
            label_text="Pasta de entrada:", 
            dialog_title="Selecionar Pasta de Entrada"
        )
        self.input_row.pack(fill="x", pady=4)
        self.input_row.var.trace_add("write", self._on_input_changed)

        # Seleção de pasta de saída
        self.output_row = FolderRow(
            self.container, 
            label_text="Pasta de saida:", 
            dialog_title="Selecionar Pasta de Saida"
        )
        self.output_row.pack(fill="x", pady=4)

        # Configurações de tamanho alvo
        dims_frame = tk.Frame(self.container, bg=Theme.CARD)
        dims_frame.pack(fill="x", pady=10)

        vcmd = (self.register(self._validate_int_or_auto), "%P")

        tk.Label(
            dims_frame, text="Tamanho Alvo (L x A):",
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED
        ).grid(row=0, column=0, sticky="w", pady=4)

        target_size_frame = tk.Frame(dims_frame, bg=Theme.CARD)
        target_size_frame.grid(row=0, column=1, sticky="w", padx=10, pady=4)

        # Entrada de Largura Alvo
        self.width_var = tk.StringVar(value="500")
        self.width_entry = tk.Entry(
            target_size_frame, textvariable=self.width_var, width=6,
            font=Theme.FONT_MAIN, bg=Theme.SURFACE, fg=Theme.TEXT,
            insertbackground=Theme.TEXT, relief="flat",
            validate="key", validatecommand=vcmd
        )
        self.width_entry.pack(side="left")

        self.width_auto = tk.BooleanVar(value=False)
        self.width_cb = tk.Checkbutton(
            target_size_frame, text="AUTO", variable=self.width_auto,
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED,
            selectcolor=Theme.SURFACE, activebackground=Theme.CARD,
            activeforeground=Theme.TEXT, command=self._toggle_width
        )
        self.width_cb.pack(side="left", padx=(4, 10))

        tk.Label(
            target_size_frame, text="x", font=Theme.FONT_BOLD,
            bg=Theme.CARD, fg=Theme.ACCENT
        ).pack(side="left", padx=2)

        # Entrada de Altura Alvo
        self.height_var = tk.StringVar(value="AUTO")
        self.height_entry = tk.Entry(
            target_size_frame, textvariable=self.height_var, width=6,
            font=Theme.FONT_MAIN, bg=Theme.SURFACE, fg=Theme.TEXT,
            insertbackground=Theme.TEXT, relief="flat",
            validate="key", validatecommand=vcmd, state="disabled"
        )
        self.height_entry.pack(side="left")

        self.height_auto = tk.BooleanVar(value=True)
        self.height_cb = tk.Checkbutton(
            target_size_frame, text="AUTO", variable=self.height_auto,
            font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED,
            selectcolor=Theme.SURFACE, activebackground=Theme.CARD,
            activeforeground=Theme.TEXT, command=self._toggle_height
        )
        self.height_cb.pack(side="left", padx=(4, 4))
        tk.Label(target_size_frame, text="px", font=Theme.FONT_LABEL, bg=Theme.CARD, fg=Theme.MUTED).pack(side="left", padx=4)

        # Configuração do Sufixo de Saída
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
            insertbackground=Theme.TEXT, relief="flat"
        )
        self.suffix_entry.pack(side="left")

        # Texto reativo explicativo (Preview do comportamento)
        self.preview_label = tk.Label(
            self.container, text="", font=Theme.FONT_LABEL,
            bg=Theme.CARD, fg=Theme.MUTED
        )
        self.preview_label.pack(anchor="w", pady=(8, 14))

        # Adiciona traces para atualizar o preview
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

    def _on_input_changed(self, *args) -> None:
        """Autopopula o campo de saída com a subpasta 'output'."""
        in_dir = self.input_row.get()
        if in_dir and not self.output_row.get():
            self.output_row.set(str(Path(in_dir) / "output"))

    @staticmethod
    def _validate_int_or_auto(value: str) -> bool:
        """Validador para permitir inteiros positivos ou AUTO."""
        return value == "" or value == "AUTO" or (value.isdigit() and int(value) >= 0)

    def _toggle_width(self) -> None:
        """Alterna a entrada da largura entre editável e AUTO."""
        if self.width_auto.get():
            self.width_entry.config(state="disabled")
            self.width_var.set("AUTO")
        else:
            self.width_entry.config(state="normal")
            self.width_var.set("500")

    def _toggle_height(self) -> None:
        """Alterna a entrada da altura entre editável e AUTO."""
        if self.height_auto.get():
            self.height_entry.config(state="disabled")
            self.height_var.set("AUTO")
        else:
            self.height_entry.config(state="normal")
            self.height_var.set("500")

    def _update_preview(self) -> None:
        """Atualiza a mensagem descritiva em tempo real com base nas opções da UI."""
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
        """Inicia o processamento assíncrono de redimensionamento em lote."""
        input_dir = self.input_row.get()
        output_dir = self.output_row.get()

        if not input_dir:
            messagebox.showwarning("Atenção", "Selecione a pasta de entrada.")
            return
        if not output_dir:
            messagebox.showwarning("Atenção", "Selecione a pasta de saída.")
            return
        if not Path(input_dir).is_dir():
            messagebox.showerror("Erro", f"Pasta de entrada não encontrada:\n{input_dir}")
            return

        # Pega a largura alvo (None = AUTO)
        target_w = None
        if not self.width_auto.get():
            try:
                target_w = int(self.width_var.get())
                if target_w <= 0: raise ValueError
            except ValueError:
                messagebox.showwarning("Atenção", "Informe uma largura alvo numérica válida maior que 0.")
                return

        # Pega a altura alvo (None = AUTO)
        target_h = None
        if not self.height_auto.get():
            try:
                target_h = int(self.height_var.get())
                if target_h <= 0: raise ValueError
            except ValueError:
                messagebox.showwarning("Atenção", "Informe uma altura alvo numérica válida maior que 0.")
                return

        suffix_pattern = self.suffix_var.get().strip()

        # Desativa a UI e limpa logs
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
                    messagebox.showinfo("Concluído", "Redimensionamento em lote concluído com sucesso!")
            self.after(0, _ui_update)

        # Roda na thread secundária
        thread = threading.Thread(
            target=process_resize_folder,
            args=(
                input_dir,
                output_dir,
                target_w,
                target_h,
                suffix_pattern,
                log_handler,
                self.progress_bar.set_progress,
                completion_handler
            ),
            daemon=True
        )
        thread.start()
