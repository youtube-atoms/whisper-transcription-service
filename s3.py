import os
import typing


def s3_download(s3, s3p: str, local_fn: str) -> str:
    def do_s3_download(s3, bucket_name: str, key: str, local_fn: str) -> str:
        dir = os.path.dirname(local_fn)
        if not os.path.exists(dir):
            os.makedirs(dir)
        assert os.path.exists(dir), 'the directory {dir} must exist'
        if os.path.exists(local_fn) :
            os.remove(local_fn)
        s3.meta.client.download_file(bucket_name, key, local_fn)
        assert os.path.exists(local_fn) , f'the local file name {local_fn} must exist'
        return local_fn

    print(f'going to download from {s3p} to {local_fn}')
    bucket, fn = s3p.split("/")[2:]
    try:
        do_s3_download(s3, bucket, fn, local_fn)
        assert os.path.exists(local_fn), "the file should be downloaded to %s, but was not." % local_fn

    except BaseException as e:
        print('something has gone horribly awry when trying to download the S3 file: %s' % e)

    return local_fn
