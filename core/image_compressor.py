import re
import unicodedata
from pathlib import Path
from PIL import Image
from core.constants import SAVE_PARAMETERS
from core.base_processor import BaseImageProcessor

class ImageCompressor(BaseImageProcessor):
    """
    Classe que implementa a otimização e compressão de imagens.
    Herda de BaseImageProcessor e suporta remoção de metadados,
    higienização de nomes para SEO e conversão simultânea para múltiplos formatos.
    """
    def __init__(
        self,
        png_compress_level: int,
        jpeg_quality: int,
        webp_quality: int,
        suffix_pattern: str,
        export_original: bool,
        export_png: bool,
        export_jpeg: bool,
        export_webp: bool,
        strip_metadata: bool,
        seo_friendly_names: bool,
        log_fn,
        progress_fn,
        done_fn
    ):
        super().__init__(log_fn, progress_fn, done_fn)
        self.png_compress_level = png_compress_level
        self.jpeg_quality = jpeg_quality
        self.webp_quality = webp_quality
        self.suffix_pattern = suffix_pattern
        self.export_original = export_original
        self.export_png = export_png
        self.export_jpeg = export_jpeg
        self.export_webp = export_webp
        self.strip_metadata = strip_metadata
        self.seo_friendly_names = seo_friendly_names

    def process_image(self, image_path: Path, output_dir: Path) -> list[Path]:
        """
        Abre a imagem, calcula as extensoes alvo de exportacao e gera os arquivos
        comprimidos e convertidos de forma paralela/simultanea para cada formato.
        """
        img = Image.open(image_path)
        original_mode = img.mode
        stem = image_path.stem
        original_suffix = image_path.suffix.lower()

        # Determina o conjunto de formatos finais para exportar
        target_suffixes = set()
        if self.export_original:
            target_suffixes.add(original_suffix)
        if self.export_png:
            target_suffixes.add(".png")
        if self.export_jpeg:
            target_suffixes.add(".jpg")
        if self.export_webp:
            target_suffixes.add(".webp")

        # Se nenhum formato estiver selecionado, usa fallback para o original
        if not target_suffixes:
            target_suffixes.add(original_suffix)

        generated_files = []

        # Processa e salva a imagem para cada formato de destino
        for target_suffix in target_suffixes:
            # Cria uma copia independente da imagem para evitar efeitos colaterais entre loops
            current_img = img.copy()
            
            # Higieniza o nome final se a opção de SEO estiver ativa
            out_stem = f"{stem}{self.suffix_pattern}"
            if self.seo_friendly_names:
                out_stem = self._sanitize_for_seo(out_stem)
                
            out_name = f"{out_stem}{target_suffix}"
            out_path = output_dir / out_name

            # Prepara argumentos de salvamento baseados nas constantes globais
            save_kwargs = SAVE_PARAMETERS.get(target_suffix, {}).copy()

            # Remove todos os metadados (EXIF, ICC, etc.) limpando o dicionario info da imagem
            if self.strip_metadata:
                current_img.info = {}
                # Garante que chaves adicionais de metadados nao vao no save do Pillow
                save_kwargs.pop("exif", None)
                save_kwargs.pop("icc_profile", None)

            # Converte o modo de cor e aplica parâmetros de acordo com o formato final
            if target_suffix == ".png":
                save_kwargs["compress_level"] = self.png_compress_level
                # Garante consistência em PNG com canal Alpha (transparência)
                if original_mode in ("RGBA", "LA", "PA"):
                    if current_img.mode != original_mode:
                        current_img = current_img.convert(original_mode)
                else:
                    if current_img.mode not in ("RGB", "L"):
                        current_img = current_img.convert("RGB")
                        
            elif target_suffix in (".jpg", ".jpeg"):
                save_kwargs["quality"] = self.jpeg_quality
                save_kwargs["subsampling"] = 0
                # JPEG não suporta transparência, então colamos a imagem sobre um fundo branco
                if current_img.mode in ("RGBA", "LA"):
                    background = Image.new("RGB", current_img.size, (255, 255, 255))
                    # Usa a própria imagem como máscara para colar
                    background.paste(current_img, mask=current_img.split()[3])
                    current_img = background
                elif current_img.mode != "RGB":
                    current_img = current_img.convert("RGB")
                    
            elif target_suffix == ".webp":
                save_kwargs["quality"] = self.webp_quality
                if self.webp_quality == 100:
                    save_kwargs["lossless"] = True
                else:
                    save_kwargs["lossless"] = False

            # Salva o arquivo final otimizado
            current_img.save(out_path, **save_kwargs)
            generated_files.append(out_path)

        return generated_files

    def _sanitize_for_seo(self, filename: str) -> str:
        """
        Higieniza o nome do arquivo para SEO: minusculo, sem acentos,
        substitui caracteres especiais e espacos por hifens.
        """
        # Converte para minúsculas
        name = filename.lower()
        # Remove acentos normalizando para decomposição unicode (NFKD)
        name = unicodedata.normalize('NFKD', name)
        name = name.encode('ascii', 'ignore').decode('utf-8')
        # Substitui qualquer coisa que não seja alfanumérica por hífen
        name = re.sub(r'[^a-z0-9]', '-', name)
        # Substitui múltiplos hífens por um único hífen
        name = re.sub(r'-+', '-', name)
        # Remove hífens no início e no fim
        name = name.strip('-')
        return name
