from pyspark.sql import SparkSession, types as T
from typing import Optional
from huggingface_hub import HfApi
from datasets import load_dataset
from itertools import islice


DOC_SCHEMA = T.StructType([
    T.StructField('dataset_id', T.StringType()),
    T.StructField('text', T.StringType()),
    T.StructField('meta', T.StringType()),
])


def list_lm_dataset_ids():
    api = HfApi()

    # TODO: How to inject the token in prod?
    datasets = api.list_datasets(
        author='bigscience-catalogue-lm-data',
        limit=None,
        use_auth_token=True,
    )

    return [ds.id for ds in datasets if 'cleaned_lm' in ds.id]


def iter_dataset(dataset_id: str):
    ds = load_dataset(dataset_id, use_auth_token=True, streaming=True)
    for row in ds['train']:
        yield dict(dataset_id=dataset_id, **row)


def main(
    limit_datasets: Optional[int] = None,
    limit_records: Optional[int] = None,
):
    spark = SparkSession.builder.getOrCreate()

    ids = list_lm_dataset_ids()
    ids = spark.sparkContext.parallelize(ids[:limit_datasets])

    df = (
        ids.flatMap(lambda ds_id: islice(iter_dataset(ds_id), limit_records))
        .toDF(DOC_SCHEMA)
    )

    return df


if __name__ == '__main__':
    main()