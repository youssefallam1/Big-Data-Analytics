"""A small MapReduce word-count engine using only Python's standard library."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
import zlib

REDUCERS = 2


def mapper(path):
    """Each input file is one split; emit (word, 1) pairs."""
    with path.open(encoding="utf-8") as source:
        for line in source:
            for word in re.findall(r"[a-z0-9]+", line.lower()):
                yield word, 1


def combine(pairs):
    """Aggregate repeated words locally in one mapper."""
    totals = {}
    for word, count in pairs:
        totals[word] = totals.get(word, 0) + count
    return totals.items()


def partition(word):
    """Use a stable hash so a word always reaches the same reducer."""
    return zlib.crc32(word.encode("utf-8")) % REDUCERS


def map_split(path):
    buckets = [[] for _ in range(REDUCERS)]
    for word, subtotal in combine(mapper(path)):
        buckets[partition(word)].append((word, subtotal))
    return buckets


def shuffle_sort(mapper_outputs):
    buckets = [[] for _ in range(REDUCERS)]
    for output in mapper_outputs:
        for reducer_id, pairs in enumerate(output):
            buckets[reducer_id].extend(pairs)
    return [sorted(bucket, key=lambda pair: pair[0]) for bucket in buckets]


def reducer(sorted_pairs):
    """Sum values for each consecutive word in a sorted partition."""
    current_word = None
    total = 0
    for word, count in sorted_pairs:
        if current_word is not None and word != current_word:
            yield current_word, total
            total = 0
        current_word = word
        total += count
    if current_word is not None:
        yield current_word, total


def run(input_dir, output_dir, pattern="*.txt"):
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    if not input_dir.is_dir():
        raise ValueError(f"Input folder does not exist: {input_dir}")
    # The supplied expected result is an answer key, never an input split.
    files = sorted(p for p in input_dir.glob(pattern)
                   if p.is_file() and p.name != "expected_word_count.txt")
    if not files:
        raise ValueError("No input files match the pattern")
    if output_dir.resolve() == input_dir.resolve():
        raise ValueError("Use different input and output folders")
    # One mapper task and one available thread per split, submitted together.
    with ThreadPoolExecutor(max_workers=len(files)) as pool:
        mapped = list(pool.map(map_split, files))
    partitions = shuffle_sort(mapped)
    output_dir.mkdir(parents=True, exist_ok=True)
    for index, pairs in enumerate(partitions):
        with (output_dir / f"part-{index:05d}.txt").open("w", encoding="utf-8") as dest:
            for word, count in reducer(pairs):
                dest.write(f"{word} {count}\n")
    return len(files)


def main():
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=base.parent / "datasets/text-files")
    parser.add_argument("--output", type=Path, default=base / "output")
    parser.add_argument("--pattern", default="*.txt")
    args = parser.parse_args()
    try:
        splits = run(args.input, args.output, args.pattern)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Error: {error}\n")
    print(f"Processed {splits} splits with {splits} mapper threads and {REDUCERS} reducers.")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
