"""Integration checks for the assignment and edge cases."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import re
from collections import Counter
from main import run, partition


def read_output(folder):
    result = {}
    files = sorted(Path(folder).glob("part-*.txt"))
    assert len(files) == 2
    for index, file in enumerate(files):
        rows = [line.split() for line in file.read_text().splitlines()]
        assert rows == sorted(rows)
        for word, count in rows:
            assert word not in result
            assert partition(word) == index
            result[word] = int(count)
    return result


class WordCountTests(unittest.TestCase):
    def test_provided_dataset(self):
        source = Path(__file__).resolve().parent.parent / "datasets/text-files"
        # Independent sequential reference; supplied answer key has inaccuracies.
        expected = Counter()
        for file in source.glob("book_*.txt"):
            expected.update(re.findall(r"[a-z0-9]+", file.read_text().lower()))
        with TemporaryDirectory() as folder:
            self.assertEqual(run(source, folder), 5)
            self.assertEqual(read_output(folder), expected)

    def test_repeated_words_punctuation_and_empty_split(self):
        with TemporaryDirectory() as folder:
            source = Path(folder) / "input"
            source.mkdir()
            (source / "a.txt").write_text("Cat, CAT! dog. 123", encoding="utf-8")
            (source / "b.txt").write_text("dog cat", encoding="utf-8")
            (source / "empty.txt").write_text("", encoding="utf-8")
            output = Path(folder) / "output"
            self.assertEqual(run(source, output), 3)
            self.assertEqual(read_output(output), {"cat": 3, "dog": 2, "123": 1})

    def test_all_empty(self):
        with TemporaryDirectory() as folder:
            source = Path(folder) / "input"
            source.mkdir()
            (source / "empty.txt").write_text("")
            output = Path(folder) / "output"
            run(source, output)
            self.assertEqual(read_output(output), {})

    def test_no_input(self):
        with TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                run(folder, Path(folder) / "output")


if __name__ == "__main__":
    unittest.main()
