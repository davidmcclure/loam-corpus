from pyspark.sql import SparkSession

from loam_corpus import load


def main():
    spark = SparkSession.builder.getOrCreate()
    df = spark.read.parquet(load.DST)
    df.printSchema()


if __name__ == '__main__':
    main()