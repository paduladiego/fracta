from pathlib import Path
from PIL import Image
from core.constants import SAVE_PARAMETERS
from core.base_processor import BaseImageProcessor

class ImageResizer(BaseImageProcessor):
    """
    Classe que implementa o redimensionamento proporcional de imagens.
    Herda de BaseImageProcessor e calcula as dimensoes de forma dinamica.
    """
    def __init__(
        self,
        target_w: int | None,
        target_h: int | None,
        suffix_pattern: str,
        log_fn,
        progress_fn,
        done_fn
    ):
        super().__init__(log_fn, progress_fn, done_fn)
        self.target_w = target_w
        self.target_h = target_h
        self.suffix_pattern = suffix_pattern

    def process_image(self, image_path: Path, output_dir: Path) -> Path:
        """
        Redimensiona a imagem mantendo a proporção de aspecto (se um dos eixos for AUTO).
        Retorna o caminho do arquivo gerado.
        """
        img = Image.open(image_path)
        original_mode = img.mode
        stem = image_path.stem
        suffix = image_path.suffix.lower()

        w, h = img.size

        # Calcula o redimensionamento mantendo o aspect ratio
        if self.target_w is not None and self.target_h is not None:
            new_w = self.target_w
            new_h = self.target_h
        elif self.target_w is not None:
            scale = self.target_w / w
            new_w = self.target_w
            new_h = max(1, int(h * scale))
        elif self.target_h is not None:
            scale = self.target_h / h
            new_w = max(1, int(w * scale))
            new_h = self.target_h
        else:
            new_w = w
            new_h = h

        # Redimensiona usando filtro de alta qualidade Lanczos
        resized_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Conversão de canais de cor
        if suffix == ".png" and original_mode in ("RGBA", "LA", "PA"):
            if resized_img.mode != original_mode:
                resized_img = resized_img.convert(original_mode)
        elif suffix in (".jpg", ".jpeg") and resized_img.mode in ("RGBA", "LA"):
            resized_img = resized_img.convert("RGB")

        # Salva o arquivo gerado
        out_name = f"{stem}{self.suffix_pattern}{suffix}"
        out_path = output_dir / out_name

        save_kwargs = SAVE_PARAMETERS.get(suffix, {})
        resized_img.save(out_path, **save_kwargs)

        return out_path
