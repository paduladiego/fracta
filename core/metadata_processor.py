import os
import json
import subprocess
from pathlib import Path
from PIL import Image
from core.constants import SUPPORTED_EXTENSIONS, SUPPORTED_VIDEO_EXTENSIONS

class MetadataProcessor:
    """
    Processador de metadados do Fracta.
    Oferece suporte para leitura, gravacao e exclusao de metadados em lote ou unitario
    para imagens (EXIF via Pillow) e videos (Tags via FFmpeg).
    """
    def __init__(self, log_fn, progress_fn, done_fn):
        self.log_fn = log_fn
        self.progress_fn = progress_fn
        self.done_fn = done_fn

    # --- Lógica de Imagens (Pillow) ---

    def _clean_exif_value(self, value) -> str:
        """
        Formata valores do EXIF de maneira limpa para exibicao humana.
        Filtra blocos binarios e arrays complexos.
        """
        if isinstance(value, (bytes, bytearray)):
            if len(value) > 150 or b'\x00' in value:
                return f"<Dados binários: {len(value)} bytes>"
            try:
                decoded = value.decode('utf-8', errors='strict')
                if all(c.isprintable() or c in '\r\n\t ' for c in decoded):
                    return decoded
                else:
                    return f"<Dados binários: {len(value)} bytes>"
            except Exception:
                try:
                    return value.decode('latin-1', errors='ignore')
                except Exception:
                    return f"<Dados binários: {len(value)} bytes>"
                    
        if isinstance(value, tuple) and len(value) > 15:
            return f"<Array de dados: {len(value)} itens>"
            
        return str(value)

    def read_image_metadata(self, image_path: Path) -> dict:
        """
        Lê tags EXIF comuns de uma imagem e retorna um dicionário amigável.
        """
        from PIL.ExifTags import TAGS
        result = {"artist": "", "copyright": "", "title": "", "software": "", "datetime": "", "camera": "", "all_exif": {}}
        try:
            with Image.open(image_path) as img:
                exif = img.getexif()
                if not exif:
                    return result
                
                # Coleta TODOS os metadados EXIF possiveis do bloco principal
                all_tags = {}
                for tag_id, value in exif.items():
                    tag_name = TAGS.get(tag_id)
                    if not tag_name or tag_name in ("MakerNote", "PrintImageMatching", "UserComment"):
                        continue
                    all_tags[tag_name] = self._clean_exif_value(value)
                
                # Mapeamento TIFF/EXIF ID das tags mais importantes:
                # Artist=315, Copyright=33432, ImageDescription=270, Software=305, DateTime=306
                # Make=271, Model=272
                make = ""
                model = ""
                
                if 315 in exif:
                    result["artist"] = str(exif[315]).strip()
                if 33432 in exif:
                    result["copyright"] = str(exif[33432]).strip()
                if 270 in exif:
                    result["title"] = str(exif[270]).strip()
                if 305 in exif:
                    result["software"] = str(exif[305]).strip()
                if 306 in exif:
                    result["datetime"] = str(exif[306]).strip()
                if 271 in exif:
                    make = str(exif[271]).strip()
                if 272 in exif:
                    model = str(exif[272]).strip()

                # Leitura do sub-IFD do EXIF (0x8769) para obter DateTimeOriginal (36867) e outras tags tecnicas
                try:
                    exif_sub = exif.get_ifd(0x8769)
                    if exif_sub:
                        for tag_id, value in exif_sub.items():
                            tag_name = TAGS.get(tag_id)
                            if not tag_name or tag_name in ("MakerNote", "PrintImageMatching", "UserComment"):
                                continue
                            all_tags[tag_name] = self._clean_exif_value(value)
                            
                        if 36867 in exif_sub and not result["datetime"]:
                            result["datetime"] = str(exif_sub[36867]).strip()
                except Exception:
                    pass

                # Combina Fabricante e Modelo para exibicao
                if make or model:
                    camera_parts = []
                    if make and make.lower() not in (model.lower() if model else ""):
                        camera_parts.append(make)
                    if model:
                        camera_parts.append(model)
                    result["camera"] = " ".join(camera_parts)
                    
                result["all_exif"] = all_tags
        except Exception as e:
            self.log_fn(f"[AVISO] Não foi possível ler EXIF de '{image_path.name}': {e}")
        return result


    def write_image_metadata(self, image_path: Path, output_dir: Path, metadata: dict, strip_all: bool) -> Path:
        """
        Escreve ou limpa tags EXIF de uma imagem e salva o resultado.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{image_path.stem}-metadata{image_path.suffix}"

        with Image.open(image_path) as img:
            if strip_all:
                # Cria um objeto EXIF limpo/vazio
                new_exif = Image.Exif()
            else:
                new_exif = img.getexif()
                # Atualiza os campos passados
                if "artist" in metadata:
                    new_exif[315] = metadata["artist"]
                if "copyright" in metadata:
                    new_exif[33432] = metadata["copyright"]
                if "title" in metadata:
                    new_exif[270] = metadata["title"]
                if "software" in metadata:
                    new_exif[305] = metadata["software"]
                if "datetime" in metadata:
                    new_exif[306] = metadata["datetime"]

            img.save(output_file, exif=new_exif)
        return output_file

    def process_image_batch(self, input_dir: str, output_dir: str, metadata: dict, strip_all: bool) -> None:
        """
        Processa edição de metadados em lote para imagens.
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        image_files = [
            f for f in input_path.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]

        if not image_files:
            self.log_fn("Nenhuma imagem suportada encontrada na pasta selecionada.")
            self.done_fn(success=False)
            return

        total = len(image_files)
        self.log_fn(f"[INFO] {total} imagem(ns) encontrada(s). Gravando metadados em lote...")

        errors = []
        for idx, img_file in enumerate(image_files, start=1):
            try:
                result = self.write_image_metadata(img_file, output_path, metadata, strip_all)
                self.log_fn(f"   [OK] '{img_file.name}' -> '{result.name}'")
            except Exception as exc:
                msg = f"   [ERRO] Falha ao gravar metadados de '{img_file.name}': {exc}"
                self.log_fn(msg)
                errors.append(msg)

            self.progress_fn(idx / total * 100)

        summary = (
            f"\n{'='*45}\n"
            f"[CONCLUIDO] {total - len(errors)}/{total} imagens processadas.\n"
            f"[SAIDA] {output_path}\n"
            f"{'='*45}"
        )
        self.log_fn(summary)
        self.done_fn(success=len(errors) == 0)

    def process_image_single(self, image_path: str, output_dir: str, metadata: dict, strip_all: bool) -> None:
        """
        Processa edicao de metadados em uma única imagem.
        """
        img_file = Path(image_path)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if not img_file.is_file() or img_file.suffix.lower() not in SUPPORTED_EXTENSIONS:
            self.log_fn(f"[ERRO] Arquivo de imagem inválido: {img_file.name}")
            self.done_fn(success=False)
            return

        self.log_fn(f"[INFO] Iniciando edição unitária de metadados para: {img_file.name}...")
        self.progress_fn(10)

        try:
            result = self.write_image_metadata(img_file, output_path, metadata, strip_all)
            self.log_fn(f"   [OK] '{img_file.name}' -> '{result.name}'")
            self.progress_fn(100)
            success = True
        except Exception as exc:
            msg = f"   [ERRO] Falha ao processar '{img_file.name}': {exc}"
            self.log_fn(msg)
            self.progress_fn(100)
            success = False

        self.done_fn(success=success)

    # --- Lógica de Vídeos (FFmpeg) ---

    def read_video_metadata(self, video_path: Path) -> dict:
        """
        Lê metadados do container de video usando o FFprobe e retorna um dicionário amigável.
        """
        result = {"artist": "", "copyright": "", "title": "", "comment": ""}
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=tags",
                "-of", "json",
                str(video_path)
            ]
            
            proc_result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo,
                check=True
            )
            
            if proc_result.stdout.strip():
                data = json.loads(proc_result.stdout)
                tags = data.get("format", {}).get("tags", {})
                
                # Mapeia chaves ignorando case-sensitivity
                tags_lower = {k.lower(): v for k, v in tags.items()}
                
                result["artist"] = tags_lower.get("artist", tags_lower.get("author", ""))
                result["copyright"] = tags_lower.get("copyright", "")
                result["title"] = tags_lower.get("title", "")
                result["comment"] = tags_lower.get("comment", tags_lower.get("description", ""))
        except Exception as e:
            self.log_fn(f"[AVISO] Não foi possível ler metadados de '{video_path.name}': {e}")
        return result

    def write_video_metadata(self, video_path: Path, output_dir: Path, metadata: dict, strip_all: bool) -> Path:
        """
        Escreve ou limpa metadados de video usando o FFmpeg com copia de fluxo (instantâneo).
        """
        from core.video_processor import VideoProcessor
        if not VideoProcessor.check_ffmpeg():
            raise RuntimeError("FFmpeg não encontrado no sistema.")

        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{video_path.stem}-metadata{video_path.suffix}"

        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(video_path)
        ]

        if strip_all:
            cmd.extend(["-map_metadata", "-1"])
        else:
            # Sobrescreve as tags desejadas
            if "artist" in metadata and metadata["artist"]:
                cmd.extend(["-metadata", f"artist={metadata['artist']}"])
                cmd.extend(["-metadata", f"author={metadata['artist']}"])
            if "copyright" in metadata and metadata["copyright"]:
                cmd.extend(["-metadata", f"copyright={metadata['copyright']}"])
            if "title" in metadata and metadata["title"]:
                cmd.extend(["-metadata", f"title={metadata['title']}"])
            if "comment" in metadata and metadata["comment"]:
                cmd.extend(["-metadata", f"comment={metadata['comment']}"])
                cmd.extend(["-metadata", f"description={metadata['comment']}"])

        # Copia os streams (sem recodificar) para execucao imediata
        cmd.extend(["-c", "copy", str(output_file)])

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo,
            check=True
        )
        return output_file

    def process_video_batch(self, input_dir: str, output_dir: str, metadata: dict, strip_all: bool) -> None:
        """
        Processa metadados em lote de videos.
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        video_files = [
            f for f in input_path.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS
        ]

        if not video_files:
            self.log_fn("Nenhum vídeo suportado encontrado na pasta selecionada.")
            self.done_fn(success=False)
            return

        total = len(video_files)
        self.log_fn(f"[INFO] {total} vídeo(s) encontrado(s). Atualizando metadados em lote...")

        errors = []
        for idx, vid_file in enumerate(video_files, start=1):
            try:
                result = self.write_video_metadata(vid_file, output_path, metadata, strip_all)
                self.log_fn(f"   [OK] '{vid_file.name}' -> '{result.name}'")
            except Exception as exc:
                msg = f"   [ERRO] Falha ao gravar metadados de '{vid_file.name}': {exc}"
                self.log_fn(msg)
                errors.append(msg)

            self.progress_fn(idx / total * 100)

        summary = (
            f"\n{'='*45}\n"
            f"[CONCLUIDO] {total - len(errors)}/{total} vídeos processados.\n"
            f"[SAIDA] {output_path}\n"
            f"{'='*45}"
        )
        self.log_fn(summary)
        self.done_fn(success=len(errors) == 0)

    def process_video_single(self, video_path: str, output_dir: str, metadata: dict, strip_all: bool) -> None:
        """
        Processa edicao de metadados em um unico video.
        """
        vid_file = Path(video_path)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if not vid_file.is_file() or vid_file.suffix.lower() not in SUPPORTED_VIDEO_EXTENSIONS:
            self.log_fn(f"[ERRO] Arquivo de vídeo inválido: {vid_file.name}")
            self.done_fn(success=False)
            return

        self.log_fn(f"[INFO] Iniciando edição unitária de metadados para: {vid_file.name}...")
        self.progress_fn(10)

        try:
            result = self.write_video_metadata(vid_file, output_path, metadata, strip_all)
            self.log_fn(f"   [OK] '{vid_file.name}' -> '{result.name}'")
            self.progress_fn(100)
            success = True
        except Exception as exc:
            msg = f"   [ERRO] Falha ao processar '{vid_file.name}': {exc}"
            self.log_fn(msg)
            self.progress_fn(100)
            success = False

        self.done_fn(success=success)
