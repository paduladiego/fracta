from abc import ABC, abstractmethod
from pathlib import Path
from core.constants import SUPPORTED_EXTENSIONS

class BaseImageProcessor(ABC):
    """
    Classe base abstrata para processamento de imagens do Fracta.
    Encapsula o gerenciamento de threads secundarias, atualizacao de progresso,
    log centralizado e iteração de diretorios em lote ou arquivo unico.
    """
    def __init__(self, log_fn, progress_fn, done_fn):
        self.log_fn = log_fn
        self.progress_fn = progress_fn
        self.done_fn = done_fn

    @abstractmethod
    def process_image(self, image_path: Path, output_dir: Path) -> Path | list[Path]:
        """
        Metodo abstrato para aplicar a manipulacao especifica na imagem.
        Deve ser implementado pelas subclasses (GridCutter, CanvasFitter, ImageResizer).
        Retorna o caminho (ou lista de caminhos) do arquivo gerado.
        """
        pass

    def process_batch(self, input_dir: str, output_dir: str) -> None:
        """
        Processa todas as imagens validas de uma pasta em lote de forma assincrona.
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Filtra apenas imagens suportadas pelo app
        image_files = [
            f for f in input_path.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]

        if not image_files:
            self.log_fn("Nenhuma imagem suportada encontrada na pasta selecionada.")
            self.done_fn(success=False)
            return

        total = len(image_files)
        self.log_fn(f"[INFO] {total} imagem(ns) encontrada(s). Iniciando processamento em lote...")

        errors = []
        for idx, img_file in enumerate(image_files, start=1):
            try:
                result = self.process_image(img_file, output_path)
                if isinstance(result, list):
                    self.log_fn(f"   [OK] '{img_file.name}': {len(result)} fatia(s) gerada(s).")
                else:
                    self.log_fn(f"   [OK] '{img_file.name}' -> '{result.name}'")
            except Exception as exc:
                msg = f"   [ERRO] Falha ao processar '{img_file.name}': {exc}"
                self.log_fn(msg)
                errors.append(msg)

            # Atualiza o percentual da barra de progresso
            self.progress_fn(idx / total * 100)

        summary = (
            f"\n{'='*45}\n"
            f"[CONCLUIDO] {total - len(errors)}/{total} imagens processadas com sucesso.\n"
            f"[SAIDA] {output_path}\n"
            f"{'='*45}"
        )
        self.log_fn(summary)
        self.done_fn(success=len(errors) == 0)

    def process_single(self, image_path: str, output_dir: str) -> None:
        """
        Processa um unico arquivo de imagem de forma isolada.
        """
        img_file = Path(image_path)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if not img_file.is_file() or img_file.suffix.lower() not in SUPPORTED_EXTENSIONS:
            self.log_fn(f"[ERRO] Arquivo de imagem invalido ou nao suportado: {img_file.name}")
            self.done_fn(success=False)
            return

        self.log_fn(f"[INFO] Iniciando processamento unitário para: {img_file.name}...")
        self.progress_fn(10) # Indica inicio da tarefa

        try:
            result = self.process_image(img_file, output_path)
            if isinstance(result, list):
                self.log_fn(f"   [OK] '{img_file.name}': {len(result)} fatia(s) gerada(s).")
            else:
                self.log_fn(f"   [OK] '{img_file.name}' -> '{result.name}'")
            self.progress_fn(100)
            success = True
        except Exception as exc:
            msg = f"   [ERRO] Falha ao processar '{img_file.name}': {exc}"
            self.log_fn(msg)
            self.progress_fn(100)
            success = False

        summary = (
            f"\n{'='*45}\n"
            f"[CONCLUIDO] Processamento unitário concluído com {'sucesso' if success else 'erro'}.\n"
            f"[SAIDA] {output_path}\n"
            f"{'='*45}"
        )
        self.log_fn(summary)
        self.done_fn(success=success)
