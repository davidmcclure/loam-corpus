from pyspark.sql import SparkSession
from itertools import islice

from loam_corpus.utils import iter_dataset


def main():
    spark = SparkSession.builder.getOrCreate()
    rows_iter = iter_dataset('laion/laion2B-en')
    print(list(islice(rows_iter, 20)))


if __name__ == '__main__':
    main()
