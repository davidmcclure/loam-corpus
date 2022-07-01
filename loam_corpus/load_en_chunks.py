import re

from pyspark.sql import SparkSession, functions as F, types as T
from boltons.iterutils import chunked

from loam_corpus import load, paths


DST = paths.env_path('en-chunks.parquet')


def split_chunks(text: str, num_tokens: int):
    tokens = list(re.finditer(r'\w+', text))

    return [
        text[c[0].start():c[-1].end()]
        for c in chunked(tokens, num_tokens)
    ]


split_chunks_udf = F.udf(T.ArrayType(T.StringType()))(split_chunks)


def main():
    spark = SparkSession.builder.getOrCreate()
    df = spark.read.parquet(load.DST)

    chunks = split_chunks_udf('text', F.lit(384))

    df = (
        df
        .filter(df.language=='en')
        .withColumn('chunk', F.explode(chunks))
        .drop('text')
    )

    df.write.parquet(DST, mode='overwrite')
    df.printSchema()


if __name__ == '__main__':
    main()