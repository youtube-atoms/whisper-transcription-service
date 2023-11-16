# Whisper Transcription Service

This project uses Whisper AI to  generate transcripts from audio files. 

usage: `pipenv run python3 main.py`

It accepts requests from whatever RabbitMQ intance you've specified, and it'll look for audio files to process in Amazon S3.
