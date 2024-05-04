import pandas as pd


def flatten_dict(d, parent_key="", sep="_"):
    """
    Flatten a nested dictionary.

    Parameters:
    - d: Dictionary to be flattened.
    - parent_key: String representing the current parent key.
    - sep: Separator to use when creating keys for nested dictionaries.

    Returns:
    - Flattened dictionary.
    """
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + str(k) if parent_key else str(k)
        if isinstance(v, dict):
            items.extend(flatten_dict(v, str(new_key), sep=sep).items())
        elif isinstance(v, list):
            for i in v:
                if isinstance(i, dict):
                    items.extend(flatten_dict(i, str(new_key), sep=sep).items())
                elif "__v" in str(new_key):
                    continue
                else:
                    items.append((str(new_key), i))
        elif "__v" in str(new_key):
            continue
        else:
            items.append((str(new_key), v))
    return dict(items)


def nested_mongodb_to_dataframe(results):
    """
    Convert nested MongoDB results into a pandas DataFrame.

    Parameters:
    - results: List of MongoDB documents (dictionaries) with nested structures.

    Returns:
    - Pandas DataFrame containing flattened MongoDB documents.
    """
    flattened_results = [flatten_dict(doc) for doc in results]

    df = pd.DataFrame.from_dict(flattened_results, orient="columns")
    df.index += 1
    return df
