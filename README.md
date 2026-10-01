# Fracta — Image & Video Batch Processor

> Ajuste, redimensione, enquadre e divida imagens e vídeos em lote com precisão máxima, alta performance e 100% offline.

[![License: MIT](https://img.shields.io/badge/Licen%C3%A7a-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Plataforma](https://img.shields.io/badge/Plataforma-Windows%20%7C%20Linux%20%7C%20macOS-blue)](https://apps.dula.one/fracta)
[![Release](https://img.shields.io/github/v/release/paduladiego/fracta?color=brightgreen&label=Vers%C3%A3o%20Oficial)](https://github.com/paduladiego/fracta/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/paduladiego/fracta/total?color=orange&label=Downloads)](https://github.com/paduladiego/fracta/releases/latest)

---

## 🌐 Links Rápidos

* 🚀 **Página Oficial:** [apps.dula.one/fracta](https://apps.dula.one/fracta)
* 📥 **Baixar Última Versão:** [Acessar Central de Downloads (Releases)](https://github.com/paduladiego/fracta/releases/latest)
* 💬 **Reportar Bug ou Sugestão:** [Abrir uma Issue](https://github.com/paduladiego/fracta/issues)

---

## 💡 O que é o Fracta?

O **Fracta** é um aplicativo desktop moderno, desenvolvido para criadores de conteúdo, e-commerces, designers e agências que precisam processar centenas ou milhares de imagens e vídeos de forma rápida, sem filas de espera e sem as limitações de ferramentas web:

1. **Cortar Grid (Fatiamento de Carrossel):**  
   Divide imagens em grades simétricas ou faixas contínuas (ex: `1x3`, `2x2`, `3x3`), perfeito para carrosséis panorâmicos de redes sociais e mapas. A nomenclatura de saída é gerada automaticamente (ex: `foto-01x01.png`, `foto-01x02.png`).

2. **Canvas Fit (Ajuste em Molduras):**  
   Centraliza e enquadra imagens proporcionalmente dentro de uma moldura de tamanho fixo (ex: `800x800` ou `1080x1080`), preservando transparências nativas ou aplicando cores sólidas de fundo (chromakey).

3. **Redimensionar (Smart Resize):**  
   Altera as dimensões de imagens em lote preservando o aspecto original. Defina uma largura ou altura fixa e utilize o modo **AUTO** na outra dimensão.

4. **Processador de Vídeos:**  
   Recorte e ajustes essenciais de clipes de vídeo com aceleração local via motor FFmpeg integrado.

---

## 🛡️ Principais Diferenciais

* 🔒 **100% Offline e Privativo:** Nenhuma imagem ou vídeo é enviado para a nuvem. Seus arquivos nunca saem do seu computador.
* ⚡ **Alta Velocidade Assíncrona:** A interface gráfica não trava enquanto processa milhares de arquivos em segundo plano.
* 🎨 **Interface Elegante:** Tema Dark Mode moderno com acompanhamento em tempo real (barra de progresso e log de eventos).
* 💎 **Qualidade Máxima de Exportação:** Preservação estrita de canais alfa (transparência RGBA em PNG e WebP) e compressão sem perda de qualidade visual.

---

## 📁 Formatos de Arquivo Suportados

| Formato | Transparência (Alpha) | Qualidade de Saída |
| :--- | :---: | :--- |
| **PNG** | ✅ Sim (RGBA) | Sem compressão (Nível 0, fidelidade total) |
| **JPG / JPEG** | ❌ Não | Qualidade máxima (100% com subsampling 0) |
| **WebP** | ✅ Sim | Modo Lossless (Sem perda) |
| **BMP** | ❌ Não | Formato raster sem perda |
| **TIFF** | ✅ Sim | Fidelidade profissional para impressão |

---

## 📥 Como Instalar e Usar

1. Acesse a aba **[Releases](../../releases/latest)** e baixe o instalador para o seu sistema:
   * **Windows:** Baixe o arquivo `.exe` (instalação com duplo clique).
2. Execute o Fracta e escolha a aba da ferramenta desejada (Grid, Canvas Fit ou Redimensionar).
3. Selecione a sua pasta com as imagens de entrada e a pasta onde deseja salvar os resultados.
4. Clique em **Iniciar Processamento** e acompanhe o progresso em tempo real!

---

## 🌍 Como Colaborar com Traduções (Community i18n)

O Fracta é um projeto feito com carinho para a comunidade e possui suporte nativo a múltiplos idiomas através de arquivos JSON simples e desacoplados na pasta [`locales/`](locales/). 

**Você pode nos ajudar a levar o Fracta para o seu idioma nativo sem precisar programar nada!**

### Passo a passo para traduzir:
1. Clique no botão **Fork** (no canto superior direito desta página) para criar uma cópia no seu GitHub.
2. Abra a pasta `locales/` no seu Fork.
3. Duplique o arquivo base `en_US.json` (ou `pt_BR.json`) e renomeie para a sigla do seu idioma:
   * Exemplos: `locales/es_ES.json` (Espanhol), `locales/fr_FR.json` (Francês), `locales/de_DE.json` (Alemão), `locales/it_IT.json` (Italiano).
4. Abra o arquivo criado e traduza os textos das mensagens, mantendo a estrutura e os nomes das chaves intactos:
   ```json
   {
     "header": {
       "settings": "Configuración",
       "about": "Acerca de"
     }
   }
   ```
5. Envie um **Pull Request (PR)** com o título: `feat(i18n): adiciona suporte ao idioma [Nome do Idioma]`.
6. Após uma breve revisão, seu idioma será incorporado na próxima versão oficial do Fracta e o seu nome/perfil receberá os devidos créditos de tradutor!

---

## 🤝 Suporte e Comunidade

* **Reportar Problemas:** Encontrou algum comportamento inesperado? Abra uma **[Issue](https://github.com/paduladiego/fracta/issues)** com detalhes.
* **Sugestões:** Ideias de novos formatos ou ferramentas? Compartilhe na aba de Issues!

---

## 👨‍💻 Desenvolvido por

Este projeto é desenvolvido e mantido pela equipe **[Dula.One](https://dula.one)**.  
* Contato oficial: `contato@dula.one`  
* Página do aplicativo: `https://apps.dula.one/fracta`

---

## ⚖️ Licença

Distribuído sob a licença **MIT** — livre para uso pessoal. Consulte o arquivo `LICENSE` para mais detalhes.
