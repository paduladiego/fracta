from pathlib import Path
from PIL import Image
from core.constants import SAVE_PARAMETERS
from core.base_processor import BaseImageProcessor

class GridCutter(BaseImageProcessor):
    """
    Classe que implementa o fatiador de imagens em grade.
    Herda de BaseImageProcessor e implementa a divisao geometrica da imagem.
    """
    def __init__(self, rows: int, cols: int, log_fn, progress_fn, done_fn):
        super().__init__(log_fn, progress_fn, done_fn)
        self.rows = rows
        self.cols = cols

    def process_image(self, image_path: Path, output_dir: Path) -> list[str]:
        """
        Divide a imagem especificada em rows x cols partes iguais.
        Retorna a lista com os caminhos dos arquivos gerados.
        """
        img = Image.open(image_path)
        original_mode = img.mode
        stem = image_path.stem
        suffix = image_path.suffix.lower()

        img_width, img_height = img.size

        # Calcula a dimensao de cada fatia
        cell_w = img_width // self.cols
        cell_h = img_height // self.rows

        generated_paths = []

        for row in range(1, self.rows + 1):
            for col in range(1, self.cols + 1):
                # Determina as coordenadas da regiao a ser recortada
                left   = (col - 1) * cell_w
                upper  = (row - 1) * cell_h
                right  = img_width  if col == self.cols else col * cell_w
                lower  = img_height if row == self.rows else row * cell_h

                # Realiza o corte
                slice_img = img.crop((left, upper, right, lower))

                # Preserva canal alpha em PNG ou converte para RGB se for JPEG
                if suffix == ".png" and original_mode in ("RGBA", "LA", "PA"):
                    if slice_img.mode != original_mode:
                        slice_img = slice_img.convert(original_mode)
                elif suffix in (".jpg", ".jpeg") and slice_img.mode in ("RGBA", "LA"):
                    slice_img = slice_img.convert("RGB")

                # Define nomenclatura
                out_name = f"{stem}-{row}x{col}{suffix}"
                out_path = output_dir / out_name

                # Aplica parametros de salvamento de alta qualidade
                save_kwargs = SAVE_PARAMETERS.get(suffix, {})
                slice_img.save(out_path, **save_kwargs)
                
                generated_paths.append(str(out_path))

        return generated_paths
