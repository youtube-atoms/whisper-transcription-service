import whisper

model = whisper.load_model('base')


def transcribe(local_fn: str) -> str:
    '''
    there's not a lot here, but it would be a shame to duplicate even this,
    knowing especially that the scope may change
    '''

    return model.transcribe(local_fn, fp16=False)['text']
