from typing import List, Set
from sack import Sack
from constants import BLANK, MAX_WORD_LENGTH, MAX_GROUP_LENGTH, MIN_GROUP_LENGTH
import os


def prepare_data(text):
    words = [set() for _ in range(MAX_WORD_LENGTH + 1)]
    for word in text.split('\n'):
        words[len(word)].add(word)
    words[0].clear()
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
    @classmethod
    def static_init(cls):
        cls.filenames = ["trios.txt", "quads.txt", "fives.txt", "sixes.txt", "sevens.txt", "eights.txt"]
        cls.directory = "text_files/"
        cls.dictionary = prepare_data(words_reader('words.txt'))

        if not os.path.isdir(cls.directory):
            os.mkdir(cls.directory)

        cls.letters = set(Sack.values_without_blank())
        cls.vowels = {'a', 'e', 'i', 'o', 'u', 'y', 'ó', 'ą', 'ę'}
        cls.consonants = {letter for letter in cls.letters if letter not in cls.vowels}
        cls.invalid_letters = {'q', 'x', 'v'}

        cls.trios = cls.load_groups(3)
        cls.quads = cls.load_groups(4)
        cls.fives = cls.load_groups(5)
        cls.sixes = cls.load_groups(6)
        cls.sevens = cls.load_groups(7)
        cls.eights = cls.load_groups(8)

        cls.groups = [cls.trios, cls.quads, cls.fives, cls.sixes, cls.sevens, cls.eights]

    @classmethod
    def find_groups(cls, length: int) -> Set[str]:
        groups = set()
        for words_by_length in cls.dictionary:
            for word in words_by_length:
                for i in range(len(word) + 1 - length):
                    group = word[i:i + length]
                    groups.add(group)

        for group in list(groups):
            if not set(group).isdisjoint(cls.invalid_letters):
                groups.remove(group)
        return groups

    @classmethod
    def load_groups(cls, length: int) -> Set[str]:
        content = words_reader(cls.directory + cls.filenames[length - MIN_GROUP_LENGTH])
        if content:
            groups = set()
            for group in content.split('\n'):
                groups.add(group)
        else:
            groups = cls.find_groups(length)
            words_writer(cls.directory + cls.filenames[length - MIN_GROUP_LENGTH], groups)
        return groups

    @classmethod
    def is_word_in_dictionary(cls, word: str) -> bool:
        return word in cls.dictionary[len(word)]

    @classmethod
    def is_in_group(cls, word: str) -> bool:
        length = len(word)
        if length < MIN_GROUP_LENGTH:
            return True
        elif length > MAX_GROUP_LENGTH:
            return False
        return word in cls.groups[length - MIN_GROUP_LENGTH]

    @classmethod
    def find_suffixes(cls, word, stem_length, max_length, min_length=1):
        suffixes = []

        if max_length and len(word) < MAX_WORD_LENGTH:
            new_word_length = len(word) + 1
            for letter in cls.letters:
                new_word = word + letter
                if cls.is_in_group(new_word[-MAX_GROUP_LENGTH:]):
                    if new_word_length - stem_length >= min_length and cls.is_word_in_dictionary(new_word):
                        suffixes.append(new_word[stem_length:])
                    suffixes.extend(cls.find_suffixes(new_word, stem_length, max_length - 1, min_length))

        return suffixes

    @classmethod
    def find_prefixes(cls, word, stem_length, max_length, min_length=1):
        prefixes = []

        if max_length and len(word) < MAX_WORD_LENGTH:
            new_word_length = len(word) + 1
            for letter in cls.letters:
                new_word = letter + word
                if cls.is_in_group(new_word[:MAX_GROUP_LENGTH]):
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
        for letter in cls.letters:
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
