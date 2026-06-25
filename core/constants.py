# Extensoes de imagem suportadas pelo aplicativo
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}

# Parametros padrao de salvamento para garantir maxima qualidade por formato
SAVE_PARAMETERS = {
    ".png": {
        "compress_level": 0  # Sem compressao para manter qualidade maxima do PNG
    },
    ".jpg": {
        "quality": 100,      # Qualidade maxima para JPEG
        "subsampling": 0     # Sem subamostragem de croma
    },
    ".jpeg": {
        "quality": 100,
        "subsampling": 0
    },
    ".webp": {
        "quality": 100,
        "lossless": True     # Modo sem perdas para WebP
    }
}
