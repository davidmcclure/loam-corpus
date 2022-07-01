import os


# TODO: Move to settings.
SPARK_ENV = os.environ.get('SPARK_ENV', 'dev')
DST_BUCKET = os.environ.get('DST_BUCKET', 'loam-corpus')
DST_PREFIX = os.environ.get('DST_PREFIX', 'v1')

# In dev, write DFs to the local filesystem; in prod, S3.
ENV_ROOT = {
    'dev': '/data/',
    'prod': 's3a://',
}

ROOT = ENV_ROOT[SPARK_ENV]


# TODO: Make it possible to pass root / bucket / prefix?
def env_path(path: str):
    return f'{ROOT}{DST_BUCKET}/{DST_PREFIX}/{path}'
