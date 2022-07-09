import re
import typer

from pyspark.sql import SparkSession, functions as F, types as T
from boltons.iterutils import chunked
from nltk.tokenize import sent_tokenize

from loam_corpus import load, paths


DST = paths.env_path('en-chunks.parquet')


def ascii_encode(text: str):
    return text.encode('ascii', 'ignore').decode()


def split_chunks(text: str, num_sents: int):
    """Split a text into a set of chunks, each containing N sentences.
    """
    sents = sent_tokenize(text)

    return [
        ' '.join(chunk)
        for chunk in chunked(sents, num_sents)
    ]


split_chunks_udf = F.udf(T.ArrayType(T.StringType()))(split_chunks)


def main(
    chunk_size: int = typer.Option(512),
    partitions: int = typer.Option(1000),
):
    spark = SparkSession.builder.getOrCreate()
    df = spark.read.parquet(load.DST)

    chunks = split_chunks_udf('text', F.lit(chunk_size))

    df = (
        df
        .filter(df.language == 'en')
        .withColumn('chunk', F.explode(chunks))
        .withColumn('chunk_id', F.monotonically_increasing_id())
        .drop('text')
        .repartition(partitions)
    )

    df.write.parquet(DST, mode='overwrite')
    df.printSchema()


if __name__ == '__main__':
    typer.run(main)
