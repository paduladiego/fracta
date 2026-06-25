from pathlib import Path
from PIL import Image
from core.constants import SAVE_PARAMETERS
from core.base_processor import BaseImageProcessor

class CanvasFitter(BaseImageProcessor):
    """
    Classe que implementa o enquadramento de imagens em molduras (Canvas Fit).
    Herda de BaseImageProcessor e encapsula a escala proporcional interna e centralização.
    """
    def __init__(
        self,
        canvas_w: int,
        canvas_h: int,
        inner_w: int | None,
        inner_h: int | None,
        bg_color: tuple,
        suffix_pattern: str,
        log_fn,
        progress_fn,
        done_fn
    ):
        super().__init__(log_fn, progress_fn, done_fn)
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h
        self.inner_w = inner_w
        self.inner_h = inner_h
        self.bg_color = bg_color
        self.suffix_pattern = suffix_pattern

    def process_image(self, image_path: Path, output_dir: Path) -> Path:
        """
        Enquadra a imagem em uma moldura de canvas_w x canvas_h centralizada.
        Retorna o caminho do arquivo gerado.
        """
        img = Image.open(image_path)
        original_mode = img.mode
        stem = image_path.stem
        suffix = image_path.suffix.lower()

        w, h = img.size

        # Determina a escala proporcional interna baseada nos limites configurados
        if self.inner_w is not None and self.inner_h is not None:
            scale = min(self.inner_w / w, self.inner_h / h)
        elif self.inner_w is not None:
            scale = self.inner_w / w
        elif self.inner_h is not None:
            scale = self.inner_h / h
        else:
            scale = min(self.canvas_w / w, self.canvas_h / h)

        # Calcula o novo tamanho garantindo tamanho minimo de 1 pixel
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))

        # Redimensiona a imagem interna com filtro Lanczos
        resized_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Cria o canvas de fundo em RGBA
        canvas = Image.new("RGBA", (self.canvas_w, self.canvas_h), self.bg_color)

        # Calcula a posição centralizada da imagem no canvas
        paste_x = (self.canvas_w - new_w) // 2
        paste_y = (self.canvas_h - new_h) // 2

        # Cola a imagem sobre o canvas mantendo a mascara de canal alpha
        mask = resized_img if resized_img.mode in ("RGBA", "LA") else None
        canvas.paste(resized_img, (paste_x, paste_y), mask)

        # Ajusta formatos e esquemas de cores
        final_img = canvas
        if suffix in (".jpg", ".jpeg"):
            # JPEG nao suporta canal alpha; convertendo para RGB
            final_img = canvas.convert("RGB")
        elif suffix == ".png" and original_mode in ("RGBA", "LA", "PA"):
            if final_img.mode != original_mode:
                final_img = final_img.convert(original_mode)

        # Salva o arquivo final
        out_name = f"{stem}{self.suffix_pattern}{suffix}"
        out_path = output_dir / out_name

        save_kwargs = SAVE_PARAMETERS.get(suffix, {})
        final_img.save(out_path, **save_kwargs)

        return out_path
