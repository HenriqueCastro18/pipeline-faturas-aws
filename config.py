import os

import boto3
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BUCKET_NAME = os.getenv("BUCKET_NAME")
SNS_TOPIC_NAME = os.getenv("SNS_TOPIC_NAME", "topico-faturas")
SQS_QUEUE_NAME = os.getenv("SQS_QUEUE_NAME", "fila-faturas")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")

session = boto3.Session(region_name=AWS_REGION)
s3 = session.client("s3")
sns = session.client("sns")
sqs = session.client("sqs")
sts = session.client("sts")

ACCOUNT_ID = sts.get_caller_identity()["Account"]
