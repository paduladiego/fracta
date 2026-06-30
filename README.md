# Fracta — Image Grid & Resizer App

> Ajuste, redimensione e divida imagens em partes de forma precisa, rápida e sem perda de qualidade.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
![Pillow](https://img.shields.io/badge/Pillow-10.x%2B-green?style=flat-square)
![Plataforma](https://img.shields.io/badge/Plataforma-Windows-lightgrey?style=flat-square)

---

## O que é o Fracta?

O **Fracta** é um aplicativo desktop com interface gráfica moderna que oferece três ferramentas fundamentais para processamento de imagens em lote:

1. **Cortar Grid (Fatiar):** Divide todas as imagens de uma pasta em grades iguais (ex: `2x2`, `3x3`, `1x4`), ideal para carrosséis do Instagram ou fatiamento de mapas.
2. **Canvas Fit (Ajustar Canvas):** Centraliza imagens dentro de uma moldura (canvas) de tamanho fixo (ex: `800x800`), escalando a imagem proporcionalmente até o limite do conteúdo interno (ex: `650xAuto` ou `Auto` para preenchimento livre), preservando fundo transparente ou aplicando cores sólidas (chromakey).
3. **Redimensionar (Resize):** Redimensiona imagens mantendo a proporção original, definindo uma dimensão fixa e a outra automática (ex: `500xAuto` ou `Auto` para preenchimento livre).

Cada imagem gerada é salva com um sufixo personalizável (por padrão `-fracta`) ou com as coordenadas de fatiamento.

---

## Funcionalidades

- Interface gráfica elegante em Dark Mode baseada em abas.
- Três modos de operação: **Cortar Grid**, **Canvas Fit** e **Redimensionar**.
- Processamento em lote de pastas inteiras de forma assíncrona (a UI não trava).
- Preservação total de transparências (modo RGBA para PNGs).
- Opção de cor de fundo sólida para formatos que não suportam transparência (como JPEG).
- Controle de dimensões automáticas (**AUTO**) para redimensionamentos responsivos.
- Barra de progresso visual e log detalhado em tempo real.
- Exportação inteligente com qualidade máxima.

---

## Formatos Suportados

| Formato | Transparência | Qualidade de Saída          |
|---------|---------------|-----------------------------|
| PNG     | Sim (RGBA)    | Sem compressão (nível 0)    |
| JPG/JPEG| Não           | quality=100, subsampling=0  |
| WebP    | Sim           | Lossless                    |
| BMP     | Não           | Sem perda                   |
| TIFF    | Sim           | Sem perda                   |

---

## Instalação

### 1. Navegue até a pasta do projeto

```powershell
cd C:\00_Projects\DividPy
```

*(Nota: O diretório físico do projeto local permanece `DividPy` ou pode ser renomeado pelo usuário para `fracta`)*

### 2. Crie e ative o ambiente virtual

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Instale as dependências

```powershell
.venv\Scripts\pip install -r requirements.txt
```

---

## Como Usar

### Iniciando o aplicativo

```powershell
.venv\Scripts\python main.py
```

### Modos de Operação

#### 1. Cortar Grid
- Selecione a pasta de entrada e a pasta de saída.
- Defina o número de linhas e colunas.
- A nomenclatura gerada será `{nome-original}-{linha}x{coluna}.{extensao}`.

#### 2. Canvas Fit
- Selecione as pastas de entrada e saída.
- Defina a dimensão do canvas externo (ex: `800`x`800`).
- Defina a dimensão limite do conteúdo interno (ex: `650`x`650` ou use **AUTO** em um dos eixos).
- Escolha a cor de fundo (transparente por padrão ou cores chromakey para JPEG).

#### 3. Redimensionar
- Defina a largura ou altura alvo e use o botão **AUTO** na outra dimensão para manter o aspecto original.

---

## Estrutura do Projeto

```
Fracta/
├── core/
│   ├── constants.py       # Definições globais de extensões e qualidades
│   ├── grid_cutter.py     # Lógica de fatiamento de imagens
│   ├── canvas_fitter.py   # Lógica de enquadramento em canvas
│   └── image_resizer.py   # Lógica de redimensionamento proporcional
├── gui/
│   ├── widgets/           # Componentes customizados da UI (Log, Progress, etc)
│   ├── tabs/              # Abas correspondentes a cada recurso do app
│   ├── theme.py           # Definição visual dark mode e estilos
│   └── app.py             # Montagem da janela principal
├── main.py                # Ponto de entrada do aplicativo
├── requirements.txt       # Dependências (Pillow)
└── README.md              # Documentação oficial
```

---

## Desenvolvido por

Este projeto foi desenvolvido e é mantido pela **[Dula.One](https://dula.one)**.

---

## Licença

MIT — livre para uso pessoal e comercial.
