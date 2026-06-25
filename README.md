# DividPy — Image Grid Cutter

> Divida imagens em partes de forma precisa, rapida e sem perda de qualidade.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
![Pillow](https://img.shields.io/badge/Pillow-12.x-green?style=flat-square)
![Plataforma](https://img.shields.io/badge/Plataforma-Windows-lightgrey?style=flat-square)

---

## O que e o DividPy?

O **DividPy** e um aplicativo desktop com interface grafica que permite cortar todas as imagens de uma pasta em partes iguais, seguindo um grid (grade) definido por voce — por exemplo, `2x2`, `3x4`, `5x1`, etc.

Cada fatia e salva com o mesmo nome da imagem original, acrescido das coordenadas da grade no formato `nome-LinhaXColuna.extensao`.

### Exemplo: grid 2x2

```
logo.png  -->  logo-1x1.png   logo-1x2.png
               logo-2x1.png   logo-2x2.png
```

---

## Funcionalidades

- Interface grafica dark mode (sem necessidade de terminal)
- Processamento em lote de toda uma pasta
- Suporte a PNG com fundo transparente (RGBA preservado)
- Suporte a JPG, WebP, BMP e TIFF
- Maxima qualidade na exportacao (sem recompressao desnecessaria)
- Barra de progresso e log em tempo real
- Thread separada (UI nao trava durante o processamento)
- Pasta de saida criada automaticamente se nao existir

---

## Formatos suportados

| Formato | Transparencia | Qualidade de saida          |
|---------|---------------|-----------------------------|
| PNG     | Sim (RGBA)    | Sem compressao (nivel 0)    |
| JPG     | Nao           | quality=100, subsampling=0  |
| WebP    | Sim           | Lossless                    |
| BMP     | Nao           | Sem perda                   |
| TIFF    | Sim           | Sem perda                   |

---

## Requisitos

- Python **3.10** ou superior
- Pillow **10.0+**

---

## Instalacao

### 1. Clone ou baixe o projeto

```powershell
# Se usar Git:
git clone https://github.com/seu-usuario/dividpy.git
cd dividpy

# Ou apenas copie a pasta do projeto para o seu computador
cd C:\00_Projects\DividPy
```

### 2. Crie o ambiente virtual

```powershell
python -m venv .venv
```

### 3. Instale as dependencias

```powershell
.venv\Scripts\pip install -r requirements.txt
```

---

## Como usar

### Iniciando o aplicativo

```powershell
.venv\Scripts\python grid_cutter.py
```

### Passo a passo na interface

```
1. Pasta de entrada
   Clique em "Procurar" e selecione a pasta que contem as imagens.
   (todas as imagens nessa pasta serao processadas)

2. Pasta de saida
   Clique em "Procurar" e escolha onde salvar as fatias.
   Dica: uma subpasta "output" e sugerida automaticamente.

3. Grid (Linhas x Colunas)
   Defina o numero de linhas e colunas do grid.
   O preview mostra quantas partes cada imagem sera dividida.

   Exemplos:
     2 x 2  =  4 partes por imagem
     3 x 3  =  9 partes por imagem
     1 x 4  =  4 fatias horizontais
     4 x 1  =  4 fatias verticais

4. Cortar Imagens
   Clique no botao roxo para iniciar.
   Acompanhe o progresso na barra e no log abaixo.
```

---

## Nomenclatura dos arquivos de saida

O padrao de nome segue o formato:

```
{nome-original}-{linha}x{coluna}.{extensao}
```

### Exemplos

| Grid | Imagem original | Arquivos gerados                                         |
|------|-----------------|----------------------------------------------------------|
| 2x2  | banner.png      | banner-1x1.png, banner-1x2.png, banner-2x1.png, banner-2x2.png |
| 1x3  | foto.jpg        | foto-1x1.jpg, foto-1x2.jpg, foto-1x3.jpg               |
| 3x1  | icon.png        | icon-1x1.png, icon-2x1.png, icon-3x1.png               |

> As coordenadas sempre seguem o padrao **Linha x Coluna**, contando a partir do canto superior esquerdo.

---

## Estrutura do projeto

```
DividPy/
├── .venv/               <- Ambiente virtual Python (nao versionar)
├── grid_cutter.py       <- Codigo principal do aplicativo
├── requirements.txt     <- Dependencias do projeto
└── README.md            <- Este arquivo
```

---

## Perguntas frequentes

**A imagem PNG com fundo transparente vai perder a transparencia?**
Nao. O modo RGBA e preservado integralmente em todas as fatias.

**O que acontece se as dimensoes nao forem divisiveis pelo grid?**
A ultima linha e/ou coluna absorve os pixels restantes, sem perder nenhum pixel da imagem original.

**Posso usar grids assimetricos como 3x7?**
Sim. Qualquer combinacao de linhas e colunas maiores que 0 e valida.

**As imagens originais sao modificadas?**
Nao. O app apenas le as imagens e salva as fatias na pasta de saida. Os arquivos originais sao intocados.

---

## Licenca

MIT — livre para uso pessoal e comercial.
