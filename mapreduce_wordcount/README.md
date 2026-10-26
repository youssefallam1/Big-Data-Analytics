# MapReduce Word Count

Python 3.9+; standard library only. No Hadoop or Spark.

## Run

From the repository root:

```bash
python mapreduce_wordcount/main.py
python -m unittest discover -s mapreduce_wordcount -v
```

For another dataset:

```bash
python mapreduce_wordcount/main.py --input path/to/texts --output path/to/results
```

Each `.txt` file is a split. `expected_word_count.txt` is excluded because it is an answer key. Use `--pattern "book_*.txt"` to select specific files.

## Implementation

1. **Map:** lowercase each line, extract alphanumeric tokens, emit `(word, 1)`.
2. **Parallel mappers:** submit one task per split to a thread pool with one available thread per split. Threads overlap work, though Python's GIL limits CPU parallelism.
3. **Combine:** sum repeated words locally using a dictionary.
4. **Partition:** `crc32(word) % 2` sends every occurrence of a word to the same reducer. The hash is stable between runs.
5. **Shuffle and sort:** collect all mapper partitions into two buckets and sort each by word.
6. **Reduce:** scan each sorted bucket and sum consecutive values. Write one sorted file per reducer: `output/part-00000.txt` and `output/part-00001.txt`.

Example: `Cat cat` and `cat dog` emit individual pairs, combine to `(cat, 2)` and `(cat, 1), (dog, 1)`, then reduce to `cat 3`, `dog 1` in their assigned output files.

## Verification

Four integration tests cover the five provided input files against an independent sequential Counter reference, repeated words across files, punctuation/case, an empty split, all-empty input, missing splits, unique reducer ownership, and sorted output.

The supplied `datasets/text-files/expected_word_count.txt` is preserved unchanged. It does not match the source texts and contains duplicate `reduce` entries. For example, source text contains `an` once and `data` twice, while the answer key lists `an 2` and `data 1`. Tests therefore use the actual input texts rather than that answer key.

## Discussion and limitations

The combiner reduces the number of pairs transferred to the shuffle stage. Stable partitioning ensures a word cannot appear in both reducer files. Each reducer output is sorted individually; concatenating the files is not necessarily globally sorted. This teaching implementation keeps intermediate pairs in memory and uses one thread per file, so it is intended for small datasets. A larger engine would use bounded workers and disk-based shuffle. Reducers run sequentially; the assignment specifically requires parallel mappers.
