import json

from config import (
    s3, sns, sqs,
    AWS_REGION, ACCOUNT_ID,
    BUCKET_NAME, SNS_TOPIC_NAME, SQS_QUEUE_NAME,
)


def criar_bucket():
    """Cria o bucket S3 onde a fatura será armazenada."""
    if AWS_REGION == "us-east-1":
        s3.create_bucket(Bucket=BUCKET_NAME) 
    else:
        s3.create_bucket(
            Bucket=BUCKET_NAME,
            CreateBucketConfiguration={"LocationConstraint": AWS_REGION},
        )
    print(f"[OK] Bucket: {BUCKET_NAME}")


def criar_topico():
    """Cria o tópico SNS e devolve o ARN dele."""
    topic_arn = sns.create_topic(Name=SNS_TOPIC_NAME)["TopicArn"]
    print(f"[OK] Tópico SNS: {topic_arn}")
    return topic_arn


def criar_fila():
    """Cria a fila SQS e devolve (url, arn)."""
    queue_url = sqs.create_queue(QueueName=SQS_QUEUE_NAME)["QueueUrl"]
    queue_arn = sqs.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=["QueueArn"]
    )["Attributes"]["QueueArn"]
    print(f"[OK] Fila SQS: {queue_arn}")
    return queue_url, queue_arn


def permitir_sns_publicar_na_fila(queue_url, queue_arn, topic_arn):
    """Dá permissão para o tópico SNS enviar mensagens para a fila SQS."""
    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "sns.amazonaws.com"},
            "Action": "sqs:SendMessage",
            "Resource": queue_arn,
            "Condition": {"ArnEquals": {"aws:SourceArn": topic_arn}},
        }],
    }
    sqs.set_queue_attributes(QueueUrl=queue_url, Attributes={"Policy": json.dumps(policy)})
    print("[OK] Permissão SNS -> SQS")


def inscrever_fila_no_topico(topic_arn, queue_arn):
    """Inscreve a fila SQS no tópico SNS (entrega da mensagem 'crua')."""
    sub = sns.subscribe(
        TopicArn=topic_arn,
        Protocol="sqs",
        Endpoint=queue_arn,
        Attributes={"RawMessageDelivery": "true"},  # payload cru = evento S3 direto
        ReturnSubscriptionArn=True,
    )
    print(f"[OK] Fila inscrita no tópico: {sub['SubscriptionArn']}")


def permitir_s3_publicar_no_topico(topic_arn):
    """Dá permissão para o bucket S3 publicar no tópico SNS."""
    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "s3.amazonaws.com"},
            "Action": "SNS:Publish",
            "Resource": topic_arn,
            "Condition": {
                "ArnLike": {"aws:SourceArn": f"arn:aws:s3:::{BUCKET_NAME}"},
                "StringEquals": {"aws:SourceAccount": ACCOUNT_ID},
            },
        }],
    }
    sns.set_topic_attributes(
        TopicArn=topic_arn, AttributeName="Policy", AttributeValue=json.dumps(policy)
    )
    print("[OK] Permissão S3 -> SNS")


def configurar_evento_s3(topic_arn):
    """Configura o bucket para publicar no SNS sempre que um objeto é criado."""
    s3.put_bucket_notification_configuration(
        Bucket=BUCKET_NAME,
        NotificationConfiguration={
            "TopicConfigurations": [{
                "TopicArn": topic_arn,
                "Events": ["s3:ObjectCreated:*"],
            }]
        },
    )
    print("[OK] Evento S3 (ObjectCreated) -> SNS")


if __name__ == "__main__":
    criar_bucket()
    topic_arn = criar_topico()
    queue_url, queue_arn = criar_fila()

    permitir_sns_publicar_na_fila(queue_url, queue_arn, topic_arn)
    inscrever_fila_no_topico(topic_arn, queue_arn)
    permitir_s3_publicar_no_topico(topic_arn)
    configurar_evento_s3(topic_arn)

    print("\nInfraestrutura provisionada com sucesso!")
