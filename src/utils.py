# function to count unique IDs
def count_unique_ids(results):
    unique_ids = set()
    for r in results:
        if r.boxes.id is not None:
            ids = r.boxes.id.int().tolist()
            unique_ids.update(ids)
    # print(f"Total unique roses tracked: {len(unique_ids)}")
    return len(unique_ids)