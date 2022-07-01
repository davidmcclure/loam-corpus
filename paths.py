import os


SPARK_ENV = os.environ.get('SPARK_ENV', 'dev')
DST_BUCKET = os.environ.get('DST_BUCKET', 'loam-corpus')
DST_PREFIX = os.environ.get('DST_PREFIX', 'v1')

# In dev, write DFs to the local filesystem; in prod, S3.
ENV_ROOT = {
    'dev': '/data/',
    'prod': 's3a://',
}


def env_path(path: str):
    root = ENV_ROOT[SPARK_ENV]
    return f'{root}{DST_BUCKET}/{DST_PREFIX}/{path}'
