#!/usr/bin/env python3
import os.path
import sys

import boto3
import tempfile
import whisper
from s3 import s3_download
import rmq
import subprocess

model = whisper.load_model('base')


def process_cli_requests(input_file: str):
    def ensure_deletion(file_name: str) -> bool:
        if os.path.exists(file_name):
            os.remove(file_name)
        return os.path.exists(file_name)

    ' shim to allow us to get transcripts locally while we build the surrounding infrastructure. '
    assert os.path.exists(input_file), 'the input file must exist'
    valid_input = None
    input_file_basename = os.path.join(os.path.dirname(input_file),
                                       f'{os.path.splitext(os.path.basename(input_file))[0]}')
    print(input_file_basename)
    for audio_file in ['.wav', '.mp3']:
        if audio_file in input_file:
            valid_input = input_file
    if valid_input is None:
        for video_file in ['.mov', '.mp4']:
            if video_file in input_file:
                new_audio_file = f'{input_file_basename}.mp3'
                ensure_deletion(new_audio_file)
                args = ['ffmpeg', '-i', f'{input_file}', f'{new_audio_file}']
                return_code = subprocess.call(args=args,
                                              env=os.environ,
                                              universal_newlines=True)
                assert return_code == 0, f'the conversion from {input_file} to {new_audio_file} should have completed successfully, but did not'
                valid_input = new_audio_file
                break

    assert valid_input is not None, 'the input file is None'
    contents: str = transcribe(valid_input)
    transcript_file = f'{input_file_basename}.txt'
    ensure_deletion(transcript_file)
    with open(transcript_file, 'w') as output:
        output.write(contents)
        print(f'wrote transcript to {transcript_file}')


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

    ## whisper

    def handle_transcription_requests(properties, payload):
        print(f'processing new request {payload} with properties {properties}')
        s3_path = payload['path']
        s3_prefix = 's3://'
        parts = s3_path[len(s3_prefix):].split('/')
        bucket, file_name = parts
        path, ext = os.path.splitext(file_name)
        local_fn = tempfile.mktemp(prefix=f'audio-to-transribe', suffix=ext)
        s3_download(s3, s3_path, local_fn)
        assert os.path.exists(local_fn), 'the file to transcribe must exist'
        return transcribe(local_fn)

    rmq.start_rabbitmq_processor(requests_q, rmq_host, rmq_username, rmq_password, rmq_vhost,
                                 handle_transcription_requests)


def transcribe(local_fn: str) -> str:
    return model.transcribe(local_fn, fp16=False)['text']


if __name__ == '__main__':
    process_rmq_requsts()
    # _, input_file = sys.argv
    # input_file = input_file.strip()
    # process_cli_requests(input_file)
