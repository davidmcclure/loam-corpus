from pyspark.sql import SparkSession
from huggingface_hub import HfApi
from datasets import load_dataset


def main():
    spark = SparkSession.builder.getOrCreate()

    api = HfApi()

    # TODO: How to inject the token in prod?
    datasets = api.list_datasets(
        author='bigscience-catalogue-lm-data',
        limit=None,
        use_auth_token=True,
    )

    print(len(datasets))

    loam_datasets = [ds for ds in datasets if 'cleaned_lm' in ds.id]

    print(len(loam_datasets))


if __name__ == '__main__':
    main()