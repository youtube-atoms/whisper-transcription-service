#!/usr/bin/env python3
import os.path

import whisper

model = whisper.load_model('base')

if __name__ == '__main__':
    import rmq

    rmq_host = 'localhost'
    rmq_vhost = ''
    rmq_username = 'myuser'
    rmq_password = 'secret'
    requests_q = 'transcription-requests'


    def handle_transcription_requests(properties, payload):
        file_path = payload['path']
        assert os.path.exists(file_path), 'the file to transcribe must exist'
        result = model.transcribe(file_path, fp16=False)
        return result['text']


    rmq.start_rabbitmq_processor(requests_q, rmq_host, rmq_username, rmq_password, rmq_vhost,
                                 handle_transcription_requests)
