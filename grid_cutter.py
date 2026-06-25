"""
DividPy - Image Grid Cutter
Divide imagens em partes baseadas em um grid definido pelo usuario.
Mantem qualidade original, incluindo transparencia de PNGs.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from PIL import Image
import threading


# -- Extensoes suportadas --
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}


def slice_image(image_path: Path, output_dir: Path, rows: int, cols: int) -> list:
    """
    Divide uma imagem em um grid de rows x cols partes.
    Retorna lista de caminhos dos arquivos gerados.
    """
    # Abre a imagem preservando o modo original (RGBA, RGB, P, etc.)
    img = Image.open(image_path)
    original_mode = img.mode
    stem = image_path.stem
    suffix = image_path.suffix.lower()

    img_width, img_height = img.size

    # Calcula tamanho de cada celula (pode haver pixels extras na ultima linha/coluna)
    cell_w = img_width // cols
    cell_h = img_height // rows

    generated = []

    for row in range(1, rows + 1):
        for col in range(1, cols + 1):
            # Calcula coordenadas exatas do crop
            left   = (col - 1) * cell_w
            upper  = (row - 1) * cell_h
            # Ultima coluna/linha absorve pixels restantes
            right  = img_width  if col == cols else col * cell_w
            lower  = img_height if row == rows else row * cell_h

            # Recorta a fatia
            slice_img = img.crop((left, upper, right, lower))

            # Garante que PNG com transparencia mantenha RGBA
            if suffix == ".png" and original_mode in ("RGBA", "LA", "PA"):
                if slice_img.mode != original_mode:
                    slice_img = slice_img.convert(original_mode)
            elif suffix in (".jpg", ".jpeg") and slice_img.mode in ("RGBA", "LA"):
                # JPG nao suporta alpha -- converte para RGB
                slice_img = slice_img.convert("RGB")

            # Nome: stem-LinhaXColuna.ext
            out_name = f"{stem}-{row}x{col}{suffix}"
            out_path = output_dir / out_name

            # Salva mantendo qualidade maxima
            save_kwargs = {}
            if suffix == ".png":
                save_kwargs["compress_level"] = 0   # sem perda de qualidade
            elif suffix in (".jpg", ".jpeg"):
                save_kwargs["quality"] = 100
                save_kwargs["subsampling"] = 0
            elif suffix == ".webp":
                save_kwargs["quality"] = 100
                save_kwargs["lossless"] = True

            slice_img.save(out_path, **save_kwargs)
            generated.append(str(out_path))

    return generated


def process_folder(input_dir, output_dir, rows, cols, log_fn, progress_fn, done_fn):
    """
    Processa todas as imagens da pasta input_dir e salva em output_dir.
    Funcoes de callback para log, progresso e finalizacao.
    """
    input_path  = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Coleta apenas arquivos de imagem suportados
    image_files = [
        f for f in input_path.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not image_files:
        log_fn("Nenhuma imagem encontrada na pasta selecionada.")
        done_fn(success=False)
        return

    total = len(image_files)
    log_fn(f"[INFO] {total} imagem(ns) encontrada(s). Iniciando corte {rows}x{cols}...")

    errors = []
    for idx, img_file in enumerate(image_files, start=1):
        try:
            log_fn(f"[CORTANDO] {img_file.name}")
            generated = slice_image(img_file, output_path, rows, cols)
            log_fn(f"   [OK] {len(generated)} fatia(s) salva(s).")
        except Exception as exc:
            msg = f"   [ERRO] '{img_file.name}': {exc}"
            log_fn(msg)
            errors.append(msg)

        # Atualiza a barra de progresso
        progress_fn(idx / total * 100)

    summary = (
        f"\n{'='*45}\n"
        f"[CONCLUIDO] {total - len(errors)}/{total} imagens processadas.\n"
        f"[SAIDA] {output_path}\n"
        f"{'='*45}"
    )
    log_fn(summary)
    done_fn(success=len(errors) == 0)


class GridCutterApp(tk.Tk):
    """Janela principal do DividPy."""

    BG         = "#0f1117"
    SURFACE    = "#1a1d27"
    CARD       = "#22263a"
    ACCENT     = "#7c6af7"
    ACCENT_HOV = "#9d8ff8"
    TEXT       = "#e8eaf0"
    MUTED      = "#8892a4"
    SUCCESS    = "#4caf7d"
    ERROR      = "#f25f5c"
    FONT_MAIN  = ("Segoe UI", 10)
    FONT_TITLE = ("Segoe UI", 18, "bold")
    FONT_LABEL = ("Segoe UI", 9)
    FONT_MONO  = ("Consolas", 9)

    def __init__(self):
        super().__init__()
        self.title("DividPy - Image Grid Cutter")
        self.geometry("700x620")
        self.minsize(600, 520)
        self.configure(bg=self.BG)
        self.resizable(True, True)
        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        """Configura estilos ttk personalizados."""
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Accent.Horizontal.TProgressbar",
            troughcolor=self.CARD,
            background=self.ACCENT,
            darkcolor=self.ACCENT,
            lightcolor=self.ACCENT,
            bordercolor=self.CARD,
            thickness=8,
        )

    def _build_ui(self):
        """Monta todos os widgets da interface."""
        root_frame = tk.Frame(self, bg=self.BG)
        root_frame.pack(fill="both", expand=True, padx=24, pady=24)

        # Titulo
        header = tk.Frame(root_frame, bg=self.BG)
        header.pack(fill="x", pady=(0, 20))
        tk.Label(
            header, text="DividPy", font=self.FONT_TITLE,
            bg=self.BG, fg=self.ACCENT
        ).pack(side="left")
        tk.Label(
            header, text="  Image Grid Cutter", font=("Segoe UI", 12),
            bg=self.BG, fg=self.MUTED
        ).pack(side="left", pady=(6, 0))

        # Card de configuracao
        card = tk.Frame(root_frame, bg=self.CARD, bd=0, relief="flat")
        card.pack(fill="x", pady=(0, 16))
        inner = tk.Frame(card, bg=self.CARD)
        inner.pack(fill="x", padx=20, pady=20)

        # Pasta de entrada
        self._input_var = tk.StringVar()
        self._make_folder_row(inner, "Pasta de entrada:", self._input_var, self._browse_input, row=0)

        # Pasta de saida
        self._output_var = tk.StringVar()
        self._make_folder_row(inner, "Pasta de saida:", self._output_var, self._browse_output, row=1)

        # Grid config
        grid_frame = tk.Frame(inner, bg=self.CARD)
        grid_frame.grid(row=2, column=0, columnspan=3, sticky="w", pady=(14, 0))

        tk.Label(
            grid_frame, text="Grid (Linhas x Colunas):",
            font=self.FONT_LABEL, bg=self.CARD, fg=self.MUTED
        ).pack(side="left")

        vcmd = (self.register(self._validate_int), "%P")

        self._rows_var = tk.StringVar(value="2")
        tk.Entry(
            grid_frame, textvariable=self._rows_var, width=4,
            font=self.FONT_MAIN, bg=self.SURFACE, fg=self.TEXT,
            insertbackground=self.TEXT, relief="flat",
            validate="key", validatecommand=vcmd,
        ).pack(side="left", padx=(10, 4))

        tk.Label(grid_frame, text="x", font=("Segoe UI", 14, "bold"),
                 bg=self.CARD, fg=self.ACCENT).pack(side="left", padx=2)

        self._cols_var = tk.StringVar(value="2")
        tk.Entry(
            grid_frame, textvariable=self._cols_var, width=4,
            font=self.FONT_MAIN, bg=self.SURFACE, fg=self.TEXT,
            insertbackground=self.TEXT, relief="flat",
            validate="key", validatecommand=vcmd,
        ).pack(side="left", padx=(4, 12))

        self._grid_preview_label = tk.Label(
            grid_frame, text="", font=self.FONT_LABEL,
            bg=self.CARD, fg=self.MUTED
        )
        self._grid_preview_label.pack(side="left")

        self._rows_var.trace_add("write", lambda *_: self._update_preview())
        self._cols_var.trace_add("write", lambda *_: self._update_preview())
        self._update_preview()

        # Botao executar
        btn_frame = tk.Frame(root_frame, bg=self.BG)
        btn_frame.pack(fill="x", pady=(0, 16))

        self._run_btn = tk.Button(
            btn_frame,
            text="Cortar Imagens",
            font=("Segoe UI", 11, "bold"),
            bg=self.ACCENT, fg="#ffffff",
            activebackground=self.ACCENT_HOV,
            activeforeground="#ffffff",
            relief="flat", cursor="hand2",
            padx=24, pady=10,
            command=self._start_processing,
        )
        self._run_btn.pack(side="left")
        self._run_btn.bind("<Enter>", lambda _: self._run_btn.config(bg=self.ACCENT_HOV))
        self._run_btn.bind("<Leave>", lambda _: self._run_btn.config(bg=self.ACCENT))

        # Barra de progresso
        progress_frame = tk.Frame(root_frame, bg=self.BG)
        progress_frame.pack(fill="x", pady=(0, 12))

        self._progress_var = tk.DoubleVar(value=0)
        ttk.Progressbar(
            progress_frame,
            style="Accent.Horizontal.TProgressbar",
            variable=self._progress_var,
            maximum=100,
        ).pack(fill="x")

        self._progress_pct_label = tk.Label(
            progress_frame, text="", font=self.FONT_LABEL,
            bg=self.BG, fg=self.MUTED
        )
        self._progress_pct_label.pack(anchor="e", pady=(4, 0))

        # Log de saida
        log_frame = tk.Frame(root_frame, bg=self.CARD, bd=0)
        log_frame.pack(fill="both", expand=True)

        tk.Label(
            log_frame, text="Log", font=self.FONT_LABEL,
            bg=self.CARD, fg=self.MUTED
        ).pack(anchor="w", padx=12, pady=(8, 0))

        text_frame = tk.Frame(log_frame, bg=self.CARD)
        text_frame.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        scrollbar = tk.Scrollbar(text_frame, bg=self.SURFACE, troughcolor=self.CARD)
        scrollbar.pack(side="right", fill="y")

        self._log_text = tk.Text(
            text_frame,
            bg=self.SURFACE, fg=self.TEXT,
            font=self.FONT_MONO,
            relief="flat", wrap="word",
            yscrollcommand=scrollbar.set,
            state="disabled",
            padx=8, pady=8,
        )
        self._log_text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self._log_text.yview)

        self._log_text.tag_config("error",   foreground=self.ERROR)
        self._log_text.tag_config("success", foreground=self.SUCCESS)
        self._log_text.tag_config("accent",  foreground=self.ACCENT)

        self._log("DividPy pronto. Configure as opcoes e clique em Cortar Imagens.", "accent")

    def _make_folder_row(self, parent, label_text, var, browse_cmd, row):
        """Cria uma linha de selecao de pasta."""
        tk.Label(
            parent, text=label_text, font=self.FONT_LABEL,
            bg=self.CARD, fg=self.MUTED, width=22, anchor="w"
        ).grid(row=row, column=0, sticky="w", pady=6)

        tk.Entry(
            parent, textvariable=var, font=self.FONT_MAIN,
            bg=self.SURFACE, fg=self.TEXT,
            insertbackground=self.TEXT, relief="flat",
        ).grid(row=row, column=1, sticky="ew", padx=(8, 8), pady=6)

        tk.Button(
            parent, text="Procurar",
            font=self.FONT_LABEL,
            bg=self.SURFACE, fg=self.ACCENT,
            activebackground=self.BG, activeforeground=self.ACCENT_HOV,
            relief="flat", cursor="hand2", padx=10, pady=4,
            command=browse_cmd,
        ).grid(row=row, column=2, pady=6)

        parent.columnconfigure(1, weight=1)

    def _browse_input(self):
        path = filedialog.askdirectory(title="Selecionar Pasta de Entrada")
        if path:
            self._input_var.set(path)
            if not self._output_var.get():
                self._output_var.set(str(Path(path) / "output"))

    def _browse_output(self):
        path = filedialog.askdirectory(title="Selecionar Pasta de Saida")
        if path:
            self._output_var.set(path)

    @staticmethod
    def _validate_int(value):
        """Permite apenas inteiros positivos nos campos de grid."""
        return value == "" or (value.isdigit() and int(value) >= 0)

    def _update_preview(self):
        """Atualiza o label de preview do grid."""
        try:
            r = int(self._rows_var.get() or 0)
            c = int(self._cols_var.get() or 0)
            if r > 0 and c > 0:
                self._grid_preview_label.config(
                    text=f"-> {r * c} parte(s) por imagem",
                    fg=self.SUCCESS if r * c <= 100 else self.ERROR
                )
            else:
                self._grid_preview_label.config(text="", fg=self.MUTED)
        except ValueError:
            self._grid_preview_label.config(text="", fg=self.MUTED)

    def _log(self, message, tag=""):
        """Adiciona mensagem ao widget de log."""
        self._log_text.configure(state="normal")
        if tag:
            self._log_text.insert("end", message + "\n", tag)
        else:
            self._log_text.insert("end", message + "\n")
        self._log_text.see("end")
        self._log_text.configure(state="disabled")

    def _set_progress(self, value):
        """Atualiza a barra de progresso (thread-safe via after)."""
        self.after(0, lambda: self._progress_var.set(value))
        self.after(0, lambda: self._progress_pct_label.config(text=f"{value:.0f}%"))

    def _start_processing(self):
        """Valida entradas e inicia o processamento em thread separada."""
        input_dir  = self._input_var.get().strip()
        output_dir = self._output_var.get().strip()

        if not input_dir:
            messagebox.showwarning("Atencao", "Selecione a pasta de entrada.")
            return
        if not output_dir:
            messagebox.showwarning("Atencao", "Selecione a pasta de saida.")
            return
        if not Path(input_dir).is_dir():
            messagebox.showerror("Erro", f"Pasta de entrada nao encontrada:\n{input_dir}")
            return

        rows_str = self._rows_var.get()
        cols_str = self._cols_var.get()

        if not rows_str or not cols_str or int(rows_str) < 1 or int(cols_str) < 1:
            messagebox.showwarning("Atencao", "Informe valores de linha e coluna maiores que 0.")
            return

        rows = int(rows_str)
        cols = int(cols_str)

        self._run_btn.config(state="disabled", text="Processando...")
        self._progress_var.set(0)
        self._progress_pct_label.config(text="0%")

        def log_safe(msg):
            tag = "error" if "[ERRO]" in msg else ("success" if "[OK]" in msg or "[CONCLUIDO]" in msg else "")
            self.after(0, lambda m=msg, t=tag: self._log(m, t))

        def on_done(success):
            def _ui():
                self._run_btn.config(state="normal", text="Cortar Imagens")
                self._progress_var.set(100)
                self._progress_pct_label.config(text="100%")
                if success:
                    messagebox.showinfo("Concluido", "Todas as imagens foram cortadas com sucesso!")
            self.after(0, _ui)

        thread = threading.Thread(
            target=process_folder,
            args=(input_dir, output_dir, rows, cols, log_safe, self._set_progress, on_done),
            daemon=True,
        )
        thread.start()


if __name__ == "__main__":
    app = GridCutterApp()
    app.mainloop()
