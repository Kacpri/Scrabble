from sack import Sack
from constants import BLANK, MAX_WORD_LENGTH
import os


def prepare_data(text):
    words = [set() for _ in range(MAX_WORD_LENGTH + 1)]
    for word in text.split('\n'):
        words[len(word)].add(word)

    return words


def words_reader(file_name):
    if os.path.exists(file_name):
        with open(file_name, "r", encoding='utf-8') as file:
            file_content = file.read()
        return file_content


def words_writer(file_name, words):
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
    def find_groups(cls, length):
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
    def load_groups(cls, size):
        content = words_reader(cls.directory + cls.filenames[size - 3])
        if content:
            groups = set()
            for group in content.split('\n'):
                groups.add(group)
        else:
            groups = cls.find_groups(size)
            words_writer(cls.directory + cls.filenames[size - 3], groups)
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
    def is_word_in_dictionary(cls, word):
        word = word.lower()
        if BLANK in word:
            for letter in Sack.values_without_blank():
                letter = letter.lower()
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
    def is_in_group(cls, word):
        length = len(word)
        if not 3 <= length <= 7:
            return False
        return word.lower() in cls.groups[length - 3]

    @classmethod
    def possible_words_with_blank(cls, pattern):
        pattern = pattern.lower()
        if BLANK not in pattern:
            return [pattern]
        words = []
        for letter in Sack.values_without_blank():
            letter = letter.lower()
            new_word = pattern.replace(BLANK, letter, 1)
            if BLANK in new_word:
                words.extend(cls.possible_words_with_blank(new_word))
            elif new_word in cls.dictionary[len(pattern)]:
                words.append(new_word)
        return words

    @classmethod
    def possible_letters(cls, pattern):
        pattern = pattern.lower()
        if BLANK not in pattern:
            return [pattern]

        words = cls.possible_words_with_blank(pattern)

        first = pattern.find(BLANK)
        last = pattern.rfind(BLANK)
        letters = []
        for word in words:
            letters.append(word[first:last + 1])

        return letters
