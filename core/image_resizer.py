import os
from pathlib import Path
from PIL import Image
from core.constants import SUPPORTED_EXTENSIONS, SAVE_PARAMETERS

def resize_image(
    image_path: Path,
    output_dir: Path,
    target_w: int | None,
    target_h: int | None,
    suffix_pattern: str = "-fracta"
) -> Path:
    """
    Redimensiona uma imagem mantendo a proporção se um dos eixos for None (AUTO).
    Se ambos forem definidos, redimensiona livremente para target_w x target_h.
    Retorna o caminho da imagem salva.
    """
    img = Image.open(image_path)
    original_mode = img.mode
    stem = image_path.stem
    suffix = image_path.suffix.lower()

    w, h = img.size

    # Determina as novas dimensões de acordo com o modo AUTO ou fixo
    if target_w is not None and target_h is not None:
        # Ambos os valores definidos, realiza o redimensionamento exato
        new_w = target_w
        new_h = target_h
    elif target_w is not None:
        # Altura e AUTO, calculada proporcionalmente
        scale = target_w / w
        new_w = target_w
        new_h = max(1, int(h * scale))
    elif target_h is not None:
        # Largura e AUTO, calculada proporcionalmente
        scale = target_h / h
        new_w = max(1, int(w * scale))
        new_h = target_h
    else:
        # Ambos os eixos sao AUTO, mantem dimensões originais
        new_w = w
        new_h = h

    # Redimensiona a imagem usando filtro Lanczos de alta qualidade
    resized_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Conversão de formato caso necessario para manter compatibilidade
    if suffix == ".png" and original_mode in ("RGBA", "LA", "PA"):
        if resized_img.mode != original_mode:
            resized_img = resized_img.convert(original_mode)
    elif suffix in (".jpg", ".jpeg") and resized_img.mode in ("RGBA", "LA"):
        resized_img = resized_img.convert("RGB")

    # Caminho de destino para salvar a imagem
    out_name = f"{stem}{suffix_pattern}{suffix}"
    out_path = output_dir / out_name

    save_kwargs = SAVE_PARAMETERS.get(suffix, {})
    resized_img.save(out_path, **save_kwargs)

    return out_path

def process_resize_folder(
    input_dir: str,
    output_dir: str,
    target_w: int | None,
    target_h: int | None,
    suffix_pattern: str,
    log_fn,
    progress_fn,
    done_fn
) -> None:
    """
    Processa todas as imagens de um diretorio redimensionando-as de forma proporcional.
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
    
    # Texto descritivo para o log de acordo com a configuracao escolhida
    mode_desc = f"{target_w if target_w else 'AUTO'}x{target_h if target_h else 'AUTO'}"
    log_fn(f"[INFO] {total} imagem(ns) encontrada(s). Redimensionando para {mode_desc}...")

    errors = []
    for idx, img_file in enumerate(image_files, start=1):
        try:
            log_fn(f"[REDIMENSIONANDO] {img_file.name}")
            out_path = resize_image(
                image_path=img_file,
                output_dir=output_path,
                target_w=target_w,
                target_h=target_h,
                suffix_pattern=suffix_pattern
            )
            log_fn(f"   [OK] Salvo em: {out_path.name}")
        except Exception as exc:
            msg = f"   [ERRO] Falha ao redimensionar '{img_file.name}': {exc}"
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
