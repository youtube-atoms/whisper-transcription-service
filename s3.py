import os
import typing


def s3_download(s3, s3p: str, local_fn: str) -> str:
    def do_s3_download(s3, bucket_name: str, key: str, local_fn: str) -> str:
        s3.meta.client.download_file(bucket_name, key, local_fn)
        assert os.path.exists(local_fn), f"the local file {local_fn} should have been downloaded"
        return local_fn

    print("going to download %s" % s3p)
    parts: typing.List[str] = s3p.split("/")
    bucket, folder, fn = parts[2:]
    try:
        do_s3_download(s3, bucket, os.path.join(folder, fn), local_fn)
        assert os.path.exists(local_fn), "the file should be downloaded to %s, but was not." % local_fn

    except BaseException as e:
        print('something has gone horribly awry when trying to download the S3 file: %s' % e)

    return local_fn
