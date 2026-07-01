import os
import re
import subprocess
from pathlib import Path
from core.constants import SUPPORTED_VIDEO_EXTENSIONS

class VideoProcessor:
    """
    Processador de videos do Fracta.
    Controla a chamada assincrona ao FFmpeg para compressao e conversao de formatos,
    detectando automaticamente a presenca dos executaveis e calculando o progresso da tarefa.
    """
    def __init__(self, log_fn, progress_fn, done_fn):
        self.log_fn = log_fn
        self.progress_fn = progress_fn
        self.done_fn = done_fn
        self.current_process = None

    @staticmethod
    def check_ffmpeg() -> bool:
        """
        Verifica se o FFmpeg esta instalado e acessivel no PATH do sistema.
        """
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
            subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                check=True
            )
            return True
        except Exception:
            return False

    @staticmethod
    def check_ffprobe() -> bool:
        """
        Verifica se o FFprobe esta instalado e acessivel no PATH do sistema.
        """
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
            subprocess.run(
                ["ffprobe", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                check=True
            )
            return True
        except Exception:
            return False

    def get_video_duration(self, video_path: Path) -> float | None:
        """
        Obtem a duracao total do video em segundos usando o FFprobe.
        """
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video_path)
            ]
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo,
                check=True
            )
            return float(result.stdout.strip())
        except Exception:
            return None

    def cancel(self) -> None:
        """
        Cancela o processo atual do FFmpeg se estiver rodando.
        """
        if self.current_process:
            try:
                self.current_process.kill()
                self.log_fn("[INFO] Processamento de vídeo interrompido pelo usuário.")
            except Exception:
                pass

    def compress_video(self, video_path: Path, output_dir: Path, format_ext: str, resolution: str, quality: str, remove_audio: bool) -> Path:
        """
        Comprime e converte um video especifico usando o FFmpeg e reporta o progresso.
        """
        if not self.check_ffmpeg():
            raise RuntimeError("FFmpeg não encontrado no sistema. Por favor, instale o FFmpeg e adicione-o ao PATH.")

        output_dir.mkdir(parents=True, exist_ok=True)
        # Nomenclatura com sufixo -fracta
        output_name = f"{video_path.stem}-fracta{format_ext}"
        output_file_path = output_dir / output_name

        # Obtem a duracao para o calculo de progresso
        duration = self.get_video_duration(video_path)
        
        # Monta os argumentos do FFmpeg
        cmd = [
            "ffmpeg",
            "-y",  # Sobrescreve se ja existir
            "-i", str(video_path)
        ]

        # Ajuste de escala (resolucao)
        if resolution == "1080p":
            cmd.extend(["-vf", "scale=-2:1080"])
        elif resolution == "720p":
            cmd.extend(["-vf", "scale=-2:720"])
        elif resolution == "480p":
            cmd.extend(["-vf", "scale=-2:480"])

        # Otimizacoes para compressao Web por formato
        if format_ext == ".mp4":
            crf = "23"  # Balanceado (padrao)
            if quality == "high":
                crf = "18"
            elif quality == "low":
                crf = "28"

            cmd.extend([
                "-c:v", "libx264",
                "-crf", crf,
                "-preset", "medium",
                "-pix_fmt", "yuv420p"  # Compatibilidade maxima com navegadores
            ])
            
            if remove_audio:
                cmd.append("-an")
            else:
                cmd.extend(["-c:a", "aac", "-b:a", "128k"])

        elif format_ext == ".webm":
            crf = "31"  # Balanceado (padrao)
            if quality == "high":
                crf = "20"
            elif quality == "low":
                crf = "40"

            cmd.extend([
                "-c:v", "libvpx-vp9",
                "-crf", crf,
                "-b:v", "0",        # Necessario para controle por CRF no VP9
                "-row-mt", "1",     # Multi-threading para melhorar performance
                "-speed", "3"       # Equilibrio de velocidade de encoding
            ])
            
            if remove_audio:
                cmd.append("-an")
            else:
                cmd.extend(["-c:a", "libopus", "-b:a", "96k"])

        cmd.append(str(output_file_path))

        # Configuracao para ocultar console cmd no Windows
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        # Inicia o processo lendo a saida de log (stderr do ffmpeg)
        self.current_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            startupinfo=startupinfo,
            bufsize=1,
            universal_newlines=True
        )

        # Expressao regular para parsear o tempo processado na saida do FFmpeg
        time_regex = re.compile(r"time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})")

        # Monitora a saida em tempo real
        while True:
            line = self.current_process.stderr.readline()
            if not line and self.current_process.poll() is not None:
                break
            
            if line:
                # Procura padrao de tempo na saida do FFmpeg para atualizar progresso
                match = time_regex.search(line)
                if match and duration:
                    hours, minutes, seconds, centiseconds = map(int, match.groups())
                    elapsed = hours * 3600 + minutes * 60 + seconds + centiseconds / 100
                    pct = min(100.0, (elapsed / duration) * 100.0)
                    self.progress_fn(pct)

        # Verifica o codigo de retorno do processo
        return_code = self.current_process.wait()
        if return_code != 0:
            # Se o processo foi abortado manualmente
            if return_code == -15 or return_code == 1:
                raise RuntimeError("Processamento interrompido ou falha no FFmpeg.")
            raise RuntimeError(f"Erro no FFmpeg. Codigo de retorno: {return_code}")

        return output_file_path

    def process_batch(self, input_dir: str, output_dir: str, format_ext: str, resolution: str, quality: str, remove_audio: bool) -> None:
        """
        Processa videos em lote de uma pasta inteira de forma assincrona.
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Filtra os videos suportados
        video_files = [
            f for f in input_path.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS
        ]

        if not video_files:
            self.log_fn("Nenhum arquivo de vídeo suportado encontrado na pasta selecionada.")
            self.done_fn(success=False)
            return

        total = len(video_files)
        self.log_fn(f"[INFO] {total} vídeo(s) encontrado(s). Iniciando processamento em lote para web...")

        errors = []
        for idx, vid_file in enumerate(video_files, start=1):
            try:
                self.log_fn(f" -> Processando [{idx}/{total}]: {vid_file.name}...")
                result = self.compress_video(
                    vid_file, output_path, format_ext, resolution, quality, remove_audio
                )
                self.log_fn(f"   [OK] '{vid_file.name}' -> '{result.name}'")
            except Exception as exc:
                msg = f"   [ERRO] Falha ao processar '{vid_file.name}': {exc}"
                self.log_fn(msg)
                errors.append(msg)

            # Atualiza o progresso global do lote
            self.progress_fn(idx / total * 100)

        summary = (
            f"\n{'='*45}\n"
            f"[CONCLUIDO] {total - len(errors)}/{total} vídeos comprimidos com sucesso para web.\n"
            f"[SAIDA] {output_path}\n"
            f"{'='*45}"
        )
        self.log_fn(summary)
        self.done_fn(success=len(errors) == 0)

    def process_single(self, video_path: str, output_dir: str, format_ext: str, resolution: str, quality: str, remove_audio: bool) -> None:
        """
        Processa um unico arquivo de video.
        """
        vid_file = Path(video_path)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if not vid_file.is_file() or vid_file.suffix.lower() not in SUPPORTED_VIDEO_EXTENSIONS:
            self.log_fn(f"[ERRO] Arquivo de vídeo inválido ou não suportado: {vid_file.name}")
            self.done_fn(success=False)
            return

        self.log_fn(f"[INFO] Iniciando compressão de vídeo unitária para: {vid_file.name}...")
        self.progress_fn(5)

        try:
            result = self.compress_video(
                vid_file, output_path, format_ext, resolution, quality, remove_audio
            )
            self.log_fn(f"   [OK] '{vid_file.name}' -> '{result.name}'")
            self.progress_fn(100)
            success = True
        except Exception as exc:
            msg = f"   [ERRO] Falha ao processar '{vid_file.name}': {exc}"
            self.log_fn(msg)
            self.progress_fn(100)
            success = False

        summary = (
            f"\n{'='*45}\n"
            f"[CONCLUIDO] Processamento de vídeo concluído com {'sucesso' if success else 'erro'}.\n"
            f"[SAIDA] {output_path}\n"
            f"{'='*45}"
        )
        self.log_fn(summary)
        self.done_fn(success=success)
