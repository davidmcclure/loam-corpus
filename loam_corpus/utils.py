from datasets import load_dataset

from loam_corpus import settings


def iter_dataset(dataset_id: str):
    ds = load_dataset(
        dataset_id,
        use_auth_token=settings.HUGGINGFACE_TOKEN,
        streaming=True,
    )

    for row in ds['train']:
        yield dict(dataset_id=dataset_id, **row)
