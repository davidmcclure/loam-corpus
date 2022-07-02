import typer

from pyspark.sql import SparkSession, types as T, functions as F
from typing import Optional
from huggingface_hub import HfApi
from datasets import load_dataset
from itertools import islice

from loam_corpus import paths


DST = paths.env_path('loam.parquet')


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


def parse_language(dataset_id: str):
    return dataset_id.split('_')[2]


def main(
    limit_datasets: Optional[int] = typer.Option(None),
    limit_records: Optional[int] = typer.Option(None),
):
    spark = SparkSession.builder.getOrCreate()

    ids = list_lm_dataset_ids()
    ids = spark.sparkContext.parallelize(ids[:limit_datasets])

    # TODO: Parse `meta`.
    df = (
        ids
        .flatMap(lambda ds_id: islice(iter_dataset(ds_id), limit_records))
        .toDF(DOC_SCHEMA)
        .withColumn('language', F.udf(parse_language)('dataset_id'))
        .withColumn('doc_id', F.monotonically_increasing_id())
    )

    df.write.parquet(DST, mode='overwrite')
    df.printSchema()


if __name__ == '__main__':
    typer.run(main)