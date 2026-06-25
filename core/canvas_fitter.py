import os
from pathlib import Path
from PIL import Image
from core.constants import SUPPORTED_EXTENSIONS, SAVE_PARAMETERS

def fit_to_canvas(
    image_path: Path,
    output_dir: Path,
    canvas_w: int,
    canvas_h: int,
    inner_w: int | None,
    inner_h: int | None,
    bg_color: tuple = (0, 0, 0, 0),
    suffix_pattern: str = "-fracta"
) -> Path:
    """
    Centraliza a imagem em um canvas de dimensões canvas_w x canvas_h.
    Redimensiona proporcionalmente a imagem interna com base em inner_w e inner_h.
    Retorna o caminho da imagem salva.
    """
    img = Image.open(image_path)
    original_mode = img.mode
    stem = image_path.stem
    suffix = image_path.suffix.lower()

    w, h = img.size

    # Determina a escala proporcional da imagem interna
    if inner_w is not None and inner_h is not None:
        # Ambos os limites definidos pelo usuario, cabe na caixa delimitadora
        scale = min(inner_w / w, inner_h / h)
    elif inner_w is not None:
        # Apenas largura limite definida (altura e livre/AUTO)
        scale = inner_w / w
    elif inner_h is not None:
        # Apenas altura limite definida (largura e livre/AUTO)
        scale = inner_h / h
    else:
        # Ambos sao AUTO, a imagem escala ate ocupar o maximo do canvas externo
        scale = min(canvas_w / w, canvas_h / h)

    # Calcula novas dimensoes garantindo o tamanho minimo de 1 pixel
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))

    # Redimensiona a imagem usando filtro de alta qualidade
    resized_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Cria o canvas de fundo
    # Utilizamos o modo RGBA para manipulação robusta de transparencias
    canvas = Image.new("RGBA", (canvas_w, canvas_h), bg_color)

    # Calcula a posição centralizada da imagem no canvas
    paste_x = (canvas_w - new_w) // 2
    paste_y = (canvas_h - new_h) // 2

    # Cola a imagem sobre o canvas mantendo a mascara de canal alpha se aplicável
    mask = resized_img if resized_img.mode in ("RGBA", "LA") else None
    canvas.paste(resized_img, (paste_x, paste_y), mask)

    # Ajustes finais dependendo do formato de saida
    final_img = canvas
    if suffix in (".jpg", ".jpeg"):
        # JPEG nao aceita RGBA. Convertemos o canvas RGBA para RGB.
        # A transparencia se tornará a cor solida bg_color informada
        final_img = canvas.convert("RGB")
    elif suffix == ".png" and original_mode in ("RGBA", "LA", "PA"):
        # Garante conservação do modo de cor original do PNG
        if final_img.mode != original_mode:
            final_img = final_img.convert(original_mode)

    # Salva o arquivo gerado
    out_name = f"{stem}{suffix_pattern}{suffix}"
    out_path = output_dir / out_name

    save_kwargs = SAVE_PARAMETERS.get(suffix, {})
    final_img.save(out_path, **save_kwargs)

    return out_path

def process_canvas_folder(
    input_dir: str,
    output_dir: str,
    canvas_w: int,
    canvas_h: int,
    inner_w: int | None,
    inner_h: int | None,
    bg_color: tuple,
    suffix_pattern: str,
    log_fn,
    progress_fn,
    done_fn
) -> None:
    """
    Processa todas as imagens da pasta aplicando a tecnica de Canvas Fit em lote.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    image_files = [
        f for f in input_path.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not image_files:
        log_fn("Nenhuma imagem suportada encontrada na pasta selecionada.")
        done_fn(success=False)
        return

    total = len(image_files)
    log_fn(f"[INFO] {total} imagem(ns) encontrada(s). Aplicando Canvas Fit {canvas_w}x{canvas_h}...")

    errors = []
    for idx, img_file in enumerate(image_files, start=1):
        try:
            log_fn(f"[AJUSTANDO] {img_file.name}")
            out_path = fit_to_canvas(
                image_path=img_file,
                output_dir=output_path,
                canvas_w=canvas_w,
                canvas_h=canvas_h,
                inner_w=inner_w,
                inner_h=inner_h,
                bg_color=bg_color,
                suffix_pattern=suffix_pattern
            )
            log_fn(f"   [OK] Salvo em: {out_path.name}")
        except Exception as exc:
            msg = f"   [ERRO] Falha ao ajustar '{img_file.name}': {exc}"
            log_fn(msg)
            errors.append(msg)

        progress_fn(idx / total * 100)

    summary = (
        f"\n{'='*45}\n"
        f"[CONCLUIDO] {total - len(errors)}/{total} imagens processadas com sucesso.\n"
        f"[SAIDA] {output_path}\n"
        f"{'='*45}"
    )
    log_fn(summary)
    done_fn(success=len(errors) == 0)
