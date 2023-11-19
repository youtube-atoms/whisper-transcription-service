#!/usr/bin/env python3
import os.path
import tempfile

import boto3

import rmq
import transcription
from s3 import s3_download


def process_rmq_requsts():
    ## configuration
    rmq_host = os.environ['RMQ_HOST']
    rmq_vhost = os.environ['RMQ_VHOST']
    rmq_username = os.environ['RMQ_USERNAME']
    rmq_password = os.environ['RMQ_PASSWORD']

    requests_q = os.environ['RMQ_TRANSCRIPTION_REQUESTS_QUEUE']

    s3_access_key = os.environ['S3_ACCESS_KEY']
    s3_access_key_secret = os.environ['S3_ACCESS_KEY_SECRET']
    s3_region = os.environ['S3_REGION']
    s3_audio_bucket = os.environ['S3_TRANSCRIPTION_AUDIO_BUCKET']

    ## aws s3
    boto3.setup_default_session(
        aws_secret_access_key=s3_access_key_secret,
        aws_access_key_id=s3_access_key,
        region_name=s3_region)
    s3 = boto3.resource("s3")

    for bucket_name in [s3_audio_bucket]:
        if len([a for a in s3.buckets.all() if a.name == bucket_name]) == 0:
            print(f'no bucket called {bucket_name} exists. creating...')
            s3.create_bucket(Bucket=bucket_name)

    def handle_transcription_requests(properties, payload):
        print(f'processing new request {payload} with properties {properties}')
        s3_path = payload['path']
        s3_prefix = 's3://'
        parts = s3_path[len(s3_prefix):].split('/')
        bucket, file_name = parts
        path, ext = os.path.splitext(file_name)
        local_fn = tempfile.mktemp(prefix=f'audio-to-transcribe', suffix=ext)
        s3_download(s3, s3_path, local_fn)
        assert os.path.exists(local_fn), 'the file to transcribe must exist'
        return transcription.transcribe(local_fn)

    rmq.start_rabbitmq_processor(requests_q, rmq_host, rmq_username, rmq_password, rmq_vhost,
                                 handle_transcription_requests)


if __name__ == '__main__':
    process_rmq_requsts()
