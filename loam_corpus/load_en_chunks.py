import re
import typer

from pyspark.sql import SparkSession, functions as F, types as T
from boltons.iterutils import chunked
from nltk.tokenize import sent_tokenize

from loam_corpus import load, paths


DST = paths.env_path('en-chunks.parquet')


@F.udf
def ascii_encode(text: str):
    return text.encode('ascii', 'ignore').decode()


@F.udf(T.ArrayType(T.StringType()))
def split_chunks(text: str, num_sents: int):
    """Split a text into a set of chunks, each containing N sentences.
    """
    sents = sent_tokenize(text)

    return [
        ' '.join(chunk)
        for chunk in chunked(sents, num_sents)
    ]


def main(
    sents_per_chunk: int = typer.Option(5),
    partitions: int = typer.Option(10_000),
):
    spark = SparkSession.builder.getOrCreate()
    df = spark.read.parquet(load.DST)

    ascii_text = ascii_encode('text')
    chunks = split_chunks(ascii_text, F.lit(sents_per_chunk))

    df = (
        df
        .filter(df.language == 'en')
        .repartition(partitions)
        .withColumn('chunk', F.explode(chunks))
        .withColumn('chunk_id', F.monotonically_increasing_id())
        .drop('text')
    )

    df.write.parquet(DST, mode='overwrite')
    df.printSchema()


if __name__ == '__main__':
    typer.run(main)
