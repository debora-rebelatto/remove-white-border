#!/usr/bin/env python3
"""
Remove bordas brancas de imagens escaneadas.
Suporta processamento em massa de uma pasta ou upload de arquivo único.

Uso:
  python remove_bordas.py --pasta ./minhas_fotos
  python remove_bordas.py --arquivo foto.jpg
  python remove_bordas.py --pasta ./fotos --tolerancia 30 --padding 5
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("Instalando dependências necessárias...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "numpy"])
    from PIL import Image
    import numpy as np


FORMATOS_SUPORTADOS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}


def remover_borda_branca(imagem: Image.Image, tolerancia: int = 20, padding: int = 0) -> Image.Image:
    """
    Remove bordas brancas de uma imagem.

    Args:
        imagem: Objeto PIL Image
        tolerancia: Quão próximo do branco (0-255) um pixel precisa ser para ser considerado borda.
                    Valores maiores removem bordas mais acinzentadas/sujas.
        padding: Pixels extras para manter ao redor do conteúdo após o corte.

    Returns:
        Imagem recortada sem as bordas brancas.
    """
    # Converte para RGBA para lidar com transparência se houver
    if imagem.mode not in ("RGB", "RGBA", "L"):
        imagem = imagem.convert("RGB")

    arr = np.array(imagem)

    # Para imagens com canal alfa, usa apenas RGB para detectar branco
    if arr.ndim == 3 and arr.shape[2] == 4:
        rgb = arr[:, :, :3]
    elif arr.ndim == 3:
        rgb = arr
    else:
        # Grayscale
        rgb = np.stack([arr, arr, arr], axis=-1)

    # Máscara de pixels que NÃO são brancos (conteúdo real)
    limite = 255 - tolerancia
    mascara_conteudo = np.any(rgb < limite, axis=-1)

    linhas_com_conteudo = np.where(mascara_conteudo.any(axis=1))[0]
    colunas_com_conteudo = np.where(mascara_conteudo.any(axis=0))[0]

    if len(linhas_com_conteudo) == 0 or len(colunas_com_conteudo) == 0:
        # Imagem completamente branca, retorna original
        return imagem

    topo    = max(0, linhas_com_conteudo[0] - padding)
    baixo   = min(arr.shape[0], linhas_com_conteudo[-1] + padding + 1)
    esquerda = max(0, colunas_com_conteudo[0] - padding)
    direita  = min(arr.shape[1], colunas_com_conteudo[-1] + padding + 1)

    return imagem.crop((esquerda, topo, direita, baixo))


def processar_arquivo(caminho_entrada: Path, caminho_saida: Path, tolerancia: int, padding: int) -> bool:
    """Processa um único arquivo de imagem."""
    try:
        with Image.open(caminho_entrada) as img:
            # Preserva metadados EXIF se existirem
            exif = img.info.get("exif", b"")

            img_processada = remover_borda_branca(img, tolerancia=tolerancia, padding=padding)

            caminho_saida.parent.mkdir(parents=True, exist_ok=True)

            salvar_kwargs = {}
            sufixo = caminho_saida.suffix.lower()
            if sufixo in (".jpg", ".jpeg"):
                salvar_kwargs["quality"] = 95
                salvar_kwargs["optimize"] = True
                if exif:
                    salvar_kwargs["exif"] = exif
            elif sufixo == ".png":
                salvar_kwargs["optimize"] = True

            img_processada.save(caminho_saida, **salvar_kwargs)

        tamanho_original = caminho_entrada.stat().st_size / 1024
        tamanho_novo = caminho_saida.stat().st_size / 1024
        print(f"  ✓ {caminho_entrada.name}  →  {img_processada.width}×{img_processada.height}px  ({tamanho_novo:.0f} KB)")
        return True

    except Exception as e:
        print(f"  ✗ {caminho_entrada.name}: {e}")
        return False


def processar_pasta(pasta_entrada: Path, pasta_saida: Path, tolerancia: int, padding: int, sobrescrever: bool):
    """Processa todos os arquivos de imagem em uma pasta."""
    arquivos = [
        f for f in sorted(pasta_entrada.rglob("*"))
        if f.is_file() and f.suffix.lower() in FORMATOS_SUPORTADOS
    ]

    if not arquivos:
        print(f"Nenhuma imagem encontrada em: {pasta_entrada}")
        return

    print(f"\n📂 Pasta: {pasta_entrada}")
    print(f"📁 Saída: {pasta_saida}")
    print(f"🖼  {len(arquivos)} imagem(ns) encontrada(s)\n")

    ok, erro = 0, 0
    for caminho in arquivos:
        # Mantém estrutura de subpastas relativa
        relativo = caminho.relative_to(pasta_entrada)
        destino = pasta_saida / relativo

        if destino.exists() and not sobrescrever:
            print(f"  – {caminho.name} (já existe, pulando)")
            continue

        if processar_arquivo(caminho, destino, tolerancia, padding):
            ok += 1
        else:
            erro += 1

    print(f"\n✅ Concluído: {ok} processada(s), {erro} erro(s).")


def main():
    parser = argparse.ArgumentParser(
        description="Remove bordas brancas de imagens escaneadas.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python remove_bordas.py --pasta ./fotos
  python remove_bordas.py --arquivo scan.jpg --tolerancia 30 --padding 10
  python remove_bordas.py --pasta ./entrada --saida ./saida --sobrescrever
        """
    )

    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--pasta",   type=Path, metavar="CAMINHO", help="Pasta com imagens para processar em massa")
    grupo.add_argument("--arquivo", type=Path, metavar="ARQUIVO",  help="Arquivo de imagem único")

    parser.add_argument(
        "--saida", type=Path, metavar="CAMINHO",
        help="Pasta de saída (padrão: <entrada>_sem_borda)"
    )
    parser.add_argument(
        "--tolerancia", type=int, default=20, metavar="0-255",
        help="Sensibilidade para detecção de branco (padrão: 20). "
             "Aumente para remover bordas acinzentadas/amareladas."
    )
    parser.add_argument(
        "--padding", type=int, default=2, metavar="PIXELS",
        help="Pixels extras para manter ao redor do conteúdo (padrão: 2)"
    )
    parser.add_argument(
        "--sobrescrever", action="store_true",
        help="Sobrescrever arquivos já existentes na pasta de saída"
    )

    args = parser.parse_args()

    # Validações
    if args.arquivo:
        if not args.arquivo.exists():
            print(f"Erro: arquivo não encontrado: {args.arquivo}")
            sys.exit(1)
        if args.arquivo.suffix.lower() not in FORMATOS_SUPORTADOS:
            print(f"Erro: formato não suportado. Use: {', '.join(FORMATOS_SUPORTADOS)}")
            sys.exit(1)

        saida = args.saida or args.arquivo.parent / (args.arquivo.stem + "_sem_borda" + args.arquivo.suffix)
        print(f"\n🖼  Processando: {args.arquivo.name}")
        processar_arquivo(args.arquivo, saida, args.tolerancia, args.padding)
        print(f"✅ Salvo em: {saida}")

    else:  # --pasta
        if not args.pasta.exists() or not args.pasta.is_dir():
            print(f"Erro: pasta não encontrada: {args.pasta}")
            sys.exit(1)

        saida = args.saida or args.pasta.parent / (args.pasta.name + "_sem_borda")
        processar_pasta(args.pasta, saida, args.tolerancia, args.padding, args.sobrescrever)


if __name__ == "__main__":
    main()
