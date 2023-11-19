import os
import subprocess
import sys

import transcription


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
                assert return_code == 0, (f'the conversion from {input_file} to {new_audio_file} should have completed '
                                          f'successfully, but did not')
                valid_input = new_audio_file
                break

    assert valid_input is not None, 'the input file is None'
    contents: str = transcription.transcribe(valid_input)
    transcript_file = f'{input_file_basename}.txt'
    ensure_deletion(transcript_file)
    with open(transcript_file, 'w') as output:
        output.write(contents)
        print(f'wrote transcript to {transcript_file}')


if __name__ == '__main__':

    _, input_file = sys.argv
    input_file = input_file.strip()
    process_cli_requests(input_file)
