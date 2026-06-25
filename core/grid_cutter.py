import os
from pathlib import Path
from PIL import Image
from core.constants import SUPPORTED_EXTENSIONS, SAVE_PARAMETERS

def slice_image(image_path: Path, output_dir: Path, rows: int, cols: int) -> list:
    """
    Divide uma imagem em um grid de rows x cols partes.
    Retorna uma lista de strings com os caminhos dos arquivos gerados.
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

    generated_paths = []

    for row in range(1, rows + 1):
        for col in range(1, cols + 1):
            # Calcula coordenadas exatas do corte (crop)
            left   = (col - 1) * cell_w
            upper  = (row - 1) * cell_h
            
            # A ultima coluna/linha absorve os pixels restantes da divisao
            right  = img_width  if col == cols else col * cell_w
            lower  = img_height if row == rows else row * cell_h

            # Realiza o recorte da regiao
            slice_img = img.crop((left, upper, right, lower))

            # Garante que PNG com transparencia mantenha o formato RGBA
            if suffix == ".png" and original_mode in ("RGBA", "LA", "PA"):
                if slice_img.mode != original_mode:
                    slice_img = slice_img.convert(original_mode)
            elif suffix in (".jpg", ".jpeg") and slice_img.mode in ("RGBA", "LA"):
                # JPEG nao possui suporte para canal alpha (transparencia), convertendo para RGB
                slice_img = slice_img.convert("RGB")

            # Nome formatado: {nome-original}-{linha}x{coluna}.{extensao}
            out_name = f"{stem}-{row}x{col}{suffix}"
            out_path = output_dir / out_name

            # Busca os parametros de salvamento ideais para o formato
            save_kwargs = SAVE_PARAMETERS.get(suffix, {})

            slice_img.save(out_path, **save_kwargs)
            generated_paths.append(str(out_path))

    return generated_paths

def process_grid_folder(
    input_dir: str, 
    output_dir: str, 
    rows: int, 
    cols: int, 
    log_fn, 
    progress_fn, 
    done_fn
) -> None:
    """
    Processa todas as imagens do diretorio input_dir e fatias em output_dir.
    Funcao de processamento assincrono executada em Thread.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Coleta apenas os arquivos de imagem com extensoes suportadas
    image_files = [
        f for f in input_path.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not image_files:
        log_fn("Nenhuma imagem suportada encontrada na pasta selecionada.")
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
            msg = f"   [ERRO] Falha ao processar '{img_file.name}': {exc}"
            log_fn(msg)
            errors.append(msg)

        # Atualiza a porcentagem de progresso
        progress_fn(idx / total * 100)

    summary = (
        f"\n{'='*45}\n"
        f"[CONCLUIDO] {total - len(errors)}/{total} imagens processadas com sucesso.\n"
        f"[SAIDA] {output_path}\n"
        f"{'='*45}"
    )
    log_fn(summary)
    done_fn(success=len(errors) == 0)
