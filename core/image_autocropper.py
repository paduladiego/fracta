from pathlib import Path
from PIL import Image, ImageChops
from core.constants import SAVE_PARAMETERS
from core.base_processor import BaseImageProcessor

class ImageAutocropper(BaseImageProcessor):
    """
    Classe que implementa a remoção de margens de cor sólida ou transparentes (autocrop).
    Herda de BaseImageProcessor e calcula a caixa delimitadora útil da imagem.
    """
    def __init__(
        self,
        trim_mode: str,
        custom_color_hex: str,
        tolerance: int,
        suffix_pattern: str,
        png_compress_level: int,
        remove_background: bool = False,
        skip_crop: bool = False,
        log_fn=None,
        progress_fn=None,
        done_fn=None
    ):
        super().__init__(log_fn, progress_fn, done_fn)
        self.trim_mode = trim_mode
        self.custom_color_hex = custom_color_hex
        self.tolerance = tolerance
        self.suffix_pattern = suffix_pattern
        self.png_compress_level = png_compress_level
        self.remove_background = remove_background
        self.skip_crop = skip_crop

    def process_image(self, image_path: Path, output_dir: Path) -> Path:
        """
        Analisa o fundo da imagem, calcula a area util e realiza o recorte.
        Retorna o caminho do arquivo gerado.
        """
        img = Image.open(image_path)
        original_mode = img.mode
        stem = image_path.stem
        suffix = image_path.suffix.lower()

        # Calcula a caixa delimitadora e a máscara do fundo
        mask, bbox = self._get_mask_and_bbox(img)

        if bbox is None:
            # Se a imagem inteira for considerada fundo, nao realiza o crop e avisa
            self.log_fn(f"   [AVISO] '{image_path.name}' foi detectada como inteiramente fundo. Nenhuma alteracao aplicada.")
            cropped_img = img
        else:
            # Se a opção de remover fundo estiver ativa e não for modo transparência
            if self.remove_background and self.trim_mode != "transparency":
                img_rgba = img.convert("RGBA")
                if "A" in img.mode:
                    orig_alpha = img.getchannel("A")
                    mask = ImageChops.darker(orig_alpha, mask)
                img_rgba.putalpha(mask)
                img = img_rgba
                suffix = ".png" # Força PNG para suportar transparência

            if self.skip_crop:
                cropped_img = img
            else:
                # Realiza o corte mantendo apenas a area util
                cropped_img = img.crop(bbox)

        # Conversao de canais de cor caso necessario ao salvar
        if suffix == ".png" and (original_mode in ("RGBA", "LA", "PA") or self.remove_background):
            if cropped_img.mode not in ("RGBA", "LA", "PA"):
                cropped_img = cropped_img.convert("RGBA")
        elif suffix in (".jpg", ".jpeg") and cropped_img.mode in ("RGBA", "LA"):
            cropped_img = cropped_img.convert("RGB")

        # Define nome de saida e salva o arquivo gerado
        out_name = f"{stem}{self.suffix_pattern}{suffix}"
        out_path = output_dir / out_name

        save_kwargs = SAVE_PARAMETERS.get(suffix, {}).copy()
        if suffix == ".png":
            save_kwargs["compress_level"] = self.png_compress_level

        cropped_img.save(out_path, **save_kwargs)

        return out_path

    def _get_mask_and_bbox(self, img: Image.Image) -> tuple[Image.Image, tuple[int, int, int, int] | None]:
        """
        Retorna a máscara da diferença (alpha) e a caixa delimitadora util (left, upper, right, lower)
        da imagem com base nas configuracoes de modo de aparamento e tolerancia.
        """
        # Se for para aparar apenas transparencia e a imagem tiver canal alpha (A)
        if self.trim_mode == "transparency" and "A" in img.mode:
            alpha = img.getchannel("A")
            if self.tolerance > 0:
                # Transforma pixels com opacidade menor/igual a tolerancia em 0 (fundo)
                alpha = alpha.point(lambda x: 0 if x <= self.tolerance else 255)
            else:
                alpha = alpha.point(lambda x: 0 if x == 0 else 255)
            return alpha, alpha.getbbox()

        # Obtem a cor de fundo a ser comparada
        bg_color = None
        if self.trim_mode == "auto":
            # Pega a cor do pixel superior esquerdo (0,0) como referencia do fundo
            bg_color = img.getpixel((0, 0))
        elif self.trim_mode == "color":
            # Converte a string hexadecimal informada para tupla RGB/RGBA compativel
            bg_color = self._hex_to_rgb(self.custom_color_hex, img.mode)

        # Se nao foi possivel obter uma cor de fundo, usa fallback de transparencia
        if bg_color is None:
            if "A" in img.mode:
                alpha = img.getchannel("A")
                return alpha, img.getbbox()
            else:
                # Caso nao haja canal alpha, define cor branca como padrao
                bg_color = (255, 255, 255)

        # Cria uma imagem solida com a cor de fundo para comparacao
        bg_img = Image.new(img.mode, img.size, bg_color)

        # Calcula a diferenca absoluta pixel a pixel
        diff = ImageChops.difference(img, bg_img)

        # Converte a diferenca para tons de cinza (L) para analise de intensidade
        diff_gray = diff.convert("L")

        if self.trim_mode == "auto":
            # Identificação de pixel (flood-fill de fora para dentro)
            if self.tolerance > 0:
                bin_mask = diff_gray.point(lambda x: 255 if x <= self.tolerance else 0)
            else:
                bin_mask = diff_gray.point(lambda x: 255 if x == 0 else 0)
                
            from PIL import ImageDraw
            w, h = bin_mask.size
            pixels = bin_mask.load()
            
            # Preenche a borda contínua de fundo (255) com um valor temporário 128
            for x in range(w):
                if pixels[x, 0] == 255:
                    ImageDraw.floodfill(bin_mask, (x, 0), 128)
                if pixels[x, h - 1] == 255:
                    ImageDraw.floodfill(bin_mask, (x, h - 1), 128)
            for y in range(h):
                if pixels[0, y] == 255:
                    ImageDraw.floodfill(bin_mask, (0, y), 128)
                if pixels[w - 1, y] == 255:
                    ImageDraw.floodfill(bin_mask, (w - 1, y), 128)
                    
            # 128 (fundo externo contíguo) vira 0 (transparente).
            # O resto (objeto e buracos internos) vira 255 (opaco).
            diff_gray = bin_mask.point(lambda x: 0 if x == 128 else 255)
            
        else:
            # Cor Sólida Específica: global (remove todos os pixels da cor)
            if self.tolerance > 0:
                diff_gray = diff_gray.point(lambda x: 0 if x <= self.tolerance else 255)
            else:
                diff_gray = diff_gray.point(lambda x: 0 if x == 0 else 255)

        return diff_gray, diff_gray.getbbox()

    def _hex_to_rgb(self, hex_str: str, mode: str) -> tuple:
        """
        Converte uma string hexadecimal de cor (ex: '#ffffff') em uma tupla
        de cor compativel com o modo de cores da imagem especificada.
        """
        hex_str = hex_str.lstrip("#")
        if len(hex_str) == 3:
            hex_str = "".join([c*2 for c in hex_str])

        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)

        if "A" in mode:
            # Retorna com canal alpha totalmente opaco por padrao para a cor de fundo
            return (r, g, b, 255)
        elif mode == "L":
            # Retorna em escala de cinza usando a formula de luminosidade padrao
            return (int(0.299 * r + 0.587 * g + 0.114 * b),)

        return (r, g, b)
