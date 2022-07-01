from pyspark.sql import SparkSession
from huggingface_hub import HfApi
from datasets import load_dataset
from itertools import islice


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
    yield from iter(ds)


def main():
    spark = SparkSession.builder.getOrCreate()

    ids = list_lm_dataset_ids()
    ids = spark.sparkContext.parallelize(ids)

    rows = ids.flatMap(lambda ds_id: islice(iter_dataset(ds_id), 100))

    return rows


if __name__ == '__main__':
    main()