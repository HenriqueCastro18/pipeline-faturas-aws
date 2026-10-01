import os
import json
from urllib.parse import unquote_plus

from config import sqs, s3, SQS_QUEUE_NAME, DOWNLOAD_DIR


def obter_url_fila():
    """Descobre a URL da fila SQS a partir do nome."""
    return sqs.get_queue_url(QueueName=SQS_QUEUE_NAME)["QueueUrl"]


def processar_payload(corpo):
    """Lê o payload da notificação e extrai (bucket, key) de cada fatura.

    O evento do S3 traz o endereço da fatura: bucket + object key.
    """
    evento = json.loads(corpo)
    faturas = []
    for registro in evento.get("Records", []):  # 'get' ignora o evento de teste do S3
        bucket = registro["s3"]["bucket"]["name"]
        key = unquote_plus(registro["s3"]["object"]["key"])  # decodifica espaços/acentos
        faturas.append((bucket, key))
    return faturas


def baixar_fatura(bucket, key):
    """Busca a fatura no S3 e baixa para a pasta local de downloads."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    destino = os.path.join(DOWNLOAD_DIR, os.path.basename(key))
    s3.download_file(bucket, key, destino)
    print(f"[OK] Fatura baixada: {destino}")
    return destino


def escutar():
    """Fica inscrito/ouvindo a fila; a cada notificação, baixa a fatura."""
    queue_url = obter_url_fila()
    print("Escutando a fila... (Ctrl+C para parar)")
    while True:
        resp = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=20,  
        )
        for msg in resp.get("Messages", []):
            try:
                for bucket, key in processar_payload(msg["Body"]):
                    baixar_fatura(bucket, key)
                sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=msg["ReceiptHandle"])
            except Exception as e:
                print(f"[ERRO] ao processar mensagem: {e}")


if __name__ == "__main__":
    escutar()
