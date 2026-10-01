import os
import sys

from config import s3, BUCKET_NAME


def ler_fatura(caminho_local):
    """Lê a fatura (PDF) do diretório local e devolve os bytes."""
    if not os.path.isfile(caminho_local):
        raise FileNotFoundError(f"Fatura não encontrada: {caminho_local}")
    with open(caminho_local, "rb") as f:
        conteudo = f.read()
    print(f"[OK] Fatura lida ({len(conteudo)} bytes): {caminho_local}")
    return conteudo


def enviar_para_s3(caminho_local, key=None):
    """Envia a fatura para o bucket S3. A 'key' é o nome do objeto no bucket."""
    key = key or os.path.basename(caminho_local)
    s3.upload_file(caminho_local, BUCKET_NAME, key)
    print(f"[OK] Fatura enviada: s3://{BUCKET_NAME}/{key}")
    return key


if __name__ == "__main__":
    caminho = sys.argv[1] if len(sys.argv) > 1 else "faturas/fatura_exemplo.pdf"
    ler_fatura(caminho)
    enviar_para_s3(caminho)
    # depois do upload o S3 dispara o evento e o resto do fluxo acontece sozinho
