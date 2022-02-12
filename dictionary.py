from typing import List, Set

from sack import Sack
from constants import BLANK, MAX_WORD_LENGTH
import os


def prepare_data(text):
    words = [set() for _ in range(MAX_WORD_LENGTH + 1)]
    for word in text.split('\n'):
        words[len(word)].add(word)

    return words


def words_reader(file_name: str):
    if os.path.exists(file_name):
        with open(file_name, "r", encoding='utf-8') as file:
            file_content = file.read()
        return file_content


def words_writer(file_name: str, words: Set[str]):
    with open(file_name, "w", encoding='utf-8') as file:
        for word in sorted(words):
            file.write(f'{word}\n')


def static_init(cls):
    if getattr(cls, "static_init", None):
        cls.static_init()
    return cls


@static_init
class Dictionary:
    filenames = ["trios.txt", "quads.txt", "fives.txt", "sixes.txt", "sevens.txt"]
    directory = "text_files/"

    data = words_reader('words.txt')
    dictionary = prepare_data(data)

    @classmethod
    def find_groups(cls, length: int) -> Set[str]:
        groups = set()
        for words_by_length in cls.dictionary:
            for word in words_by_length:
                for i in range(len(word) + 1 - length):
                    group = word[i:i + length]
                    groups.add(group)

        impossible_letters = {'v', 'x', 'q'}
        for group in list(groups):
            if not set(group).isdisjoint(impossible_letters):
                groups.remove(group)
        return groups

    @classmethod
    def load_groups(cls, length: int) -> Set[str]:
        content = words_reader(cls.directory + cls.filenames[length - 3])
        if content:
            groups = set()
            for group in content.split('\n'):
                groups.add(group)
        else:
            groups = cls.find_groups(length)
            words_writer(cls.directory + cls.filenames[length - 3], groups)
        return groups

    if not os.path.isdir(directory):
        os.mkdir(directory)

    @classmethod
    def static_init(cls):
        cls.trios = cls.load_groups(3)
        cls.quads = cls.load_groups(4)
        cls.fives = cls.load_groups(5)
        cls.sixes = cls.load_groups(6)
        cls.sevens = cls.load_groups(7)
        cls.groups = [cls.trios, cls.quads, cls.fives, cls.sixes, cls.sevens]

    @classmethod
    def is_word_in_dictionary(cls, word: str) -> bool:
        if BLANK in word:
            for letter in Sack.values_without_blank():
                new_word = word.replace(BLANK, letter, 1)
                if BLANK in new_word:
                    if cls.is_word_in_dictionary(new_word):
                        return True
                elif new_word in cls.dictionary[len(word)]:
                    return True
        if word in cls.dictionary[len(word)]:
            return True
        return False

    @classmethod
    def is_in_group(cls, word: str) -> bool:
        length = len(word)
        if length < 3:
            return True
        elif length > 7:
            return False
        return word in cls.groups[length - 3]

    @classmethod
    def find_suffixes(cls, word, stem_length, max_length, min_length=1):
        suffixes = []

        if max_length and len(word) < MAX_WORD_LENGTH:
            new_word_length = len(word) + 1
            for letter in Sack.values_without_blank():
                new_word = word + letter
                if cls.is_in_group(new_word[-7:]):
                    if new_word_length - stem_length >= min_length and cls.is_word_in_dictionary(new_word):
                        suffixes.append(new_word[stem_length:])
                    suffixes.extend(cls.find_suffixes(new_word, stem_length, max_length - 1, min_length))

        return suffixes

    @classmethod
    def find_prefixes(cls, word, stem_length, max_length, min_length=1):
        prefixes = []

        if max_length and len(word) < MAX_WORD_LENGTH:
            new_word_length = len(word) + 1
            for letter in Sack.values_without_blank():
                new_word = letter + word
                if cls.is_in_group(new_word[:7]):
                    if new_word_length - stem_length >= min_length and cls.is_word_in_dictionary(new_word):
                        prefixes.append(new_word[:-stem_length])
                    prefixes.extend(cls.find_prefixes(new_word, stem_length, max_length - 1, min_length))

        return prefixes

    @classmethod
    def possible_words_with_blank(cls, pattern: str) -> List[str]:
        pattern = pattern
        if BLANK not in pattern:
            return [pattern]
        words = []
        for letter in Sack.values_without_blank():
            new_word = pattern.replace(BLANK, letter, 1)
            if BLANK in new_word:
                words.extend(cls.possible_words_with_blank(new_word))
            elif new_word in cls.dictionary[len(pattern)]:
                words.append(new_word)
        return words

    @classmethod
    def possible_letters(cls, pattern: str) -> List[str]:
        pattern = pattern
        if BLANK not in pattern:
            return [pattern]

        words = cls.possible_words_with_blank(pattern)

        first = pattern.find(BLANK)
        last = pattern.rfind(BLANK)
        letters = []
        for word in words:
            letters.append(word[first:last + 1])

        return letters
