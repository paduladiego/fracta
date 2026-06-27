import sys
import os
import platform
import json
import urllib.request
from core.constants import UPDATE_JSON_URL

class AppUpdater:
    """
    Classe responsavel por verificar atualizacoes remotas e identificar a plataforma ativa.
    """
    @staticmethod
    def detect_platform() -> str:
        """
        Detecta e retorna a plataforma de execucao do aplicativo:
        'windows', 'linux', 'android' ou 'web'.
        """
        # Verifica se esta rodando em ambiente Android (Kivy / PySide / etc)
        if "ANDROID_ARGUMENT" in os.environ or sys.platform == "android":
            return "android"
            
        # Verifica se esta rodando em ambiente Web (WebAssembly / Pyodide / Emscripten)
        if sys.platform in ("emscripten", "wasm32") or "pyodide" in sys.modules:
            return "web"
            
        # Detecta sistemas desktop tradicionais
        system = platform.system().lower()
        if "windows" in system:
            return "windows"
        elif "linux" in system:
            return "linux"
            
        return "unknown"

    @classmethod
    def check_for_updates(cls, current_version: str) -> dict | None:
        """
        Faz uma requisicao silenciosa na URL remota de atualizacoes e
        compara a versao local com a versao mais recente.
        Retorna o dicionario de dados da atualizacao se houver versao superior.
        """
        platform_name = cls.detect_platform()
        
        # Na Web as atualizacoes sao de carregamento direto, sem necessidade de aviso
        if platform_name == "web":
            return None

        try:
            # Faz requisicao HTTP GET com timeout de 3 segundos para evitar travamentos
            req = urllib.request.Request(
                UPDATE_JSON_URL, 
                headers={"User-Agent": "Fracta-App-Updater"}
            )
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode("utf-8"))
                
            latest_version = data.get("latest_version")
            if not latest_version:
                return None
                
            # Compara as versoes convertendo para tuplas numericas (Ex: '1.0.0' -> (1, 0, 0))
            local_parts = tuple(map(int, current_version.split(".")))
            latest_parts = tuple(map(int, latest_version.split(".")))
            
            if latest_parts > local_parts:
                # Extrai a URL de download correspondente a plataforma ativa
                download_urls = data.get("download_urls", {})
                download_url = download_urls.get(platform_name)
                
                # Se nao houver URL especifica para a plataforma, usa fallback geral
                if not download_url:
                    download_url = download_urls.get("windows") or "https://github.com/paduladiego/fracta"
                
                return {
                    "latest_version": latest_version,
                    "changelog": data.get("changelog", "Melhorias gerais de estabilidade."),
                    "download_url": download_url,
                    "platform": platform_name
                }
        except Exception:
            # Falhas de conexao, DNS ou JSON sao tratadas silenciosamente sem afetar o app
            return None

        return None
