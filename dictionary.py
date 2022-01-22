from itertools import permutations
from sack import Sack
from constants import BLANK
import os

filenames = ["quads.txt", "fives.txt", "sixes.txt", "sevens.txt"]
directory = "text_files/"


def prepare_data(text):
    words = [set() for _ in range(16)]
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


data = words_reader('words.txt')
dictionary = prepare_data(data)


def find_groups(length):
    groups = set()
    for words_by_length in dictionary:
        for word in words_by_length:
            for i in range(len(word) + 1 - length):
                group = word[i:i + length]
                if not any(letter in group for letter in ['v', 'x', 'q']):
                    groups.add(group)
    return groups


def load_groups(size):
    groups = []
    content = words_reader(directory + filenames[size - 4])
    if content:
        for group in content.split('\n'):
            groups.append(group)
    else:
        groups = find_groups(size)
        words_writer(directory + filenames[size - 4], groups)
    return groups


if not os.path.isdir(directory):
    os.mkdir(directory)
quads = load_groups(4)
fives = load_groups(5)
sixes = load_groups(6)
sevens = load_groups(7)


def is_word_in_dictionary(word):
    word = word.lower()
    if BLANK in word:
        for letter in Sack.values_without_blank():
            letter = letter.lower()
            new_word = word.replace(BLANK, letter, 1)
            if BLANK in new_word:
                if is_word_in_dictionary(new_word):
                    return True
            elif new_word in dictionary[len(word)]:
                return True
    if word in dictionary[len(word)]:
        return True
    return False


def is_in_group(word):
    length = len(word)
    if length == 4:
        group = quads
    elif length == 5:
        group = fives
    elif length == 6:
        group = sixes
    elif length == 7:
        group = sevens
    else:
        return False
    return word.lower() in group


def possible_words_with_blank(word, find_letters=False):
    word = word.lower()
    if BLANK not in word:
        return word
    words = []
    for letter in Sack.values_without_blank():
        letter = letter.lower()
        new_word = word.replace(BLANK, letter, 1)
        if BLANK in new_word:
            words.extend(possible_words_with_blank(new_word))
        elif new_word in dictionary[len(word)]:
            words.append(letter if find_letters else new_word)
    return words


def possible_letters(pattern):
    return possible_words_with_blank(pattern, True)


def find_words(rack):
    words = [set() for _ in range(len(rack) + 1)]
    for length in range(2, len(rack) + 1):
        for permutation in permutations(rack, length):
            word = ''.join(permutation).lower()
            if is_word_in_dictionary(word):
                words[length].add(word)


def find_words_with_letters_on_board(rack, on_board, max_length_left, max_length_right):
    words = [set() for _ in range(len(rack) + len(on_board) + 1)]

    for length in range(1, len(rack) + 1):
        for permutation in permutations(rack, length):
            permutation = ''.join(permutation)
            for length_left in range(max_length_left + 1):
                length_right = length - length_left
                if length_right > max_length_right:
                    continue
                word = permutation[:length_left] + on_board + permutation[length_left:]
                word = word.lower()
                if is_word_in_dictionary(word):
                    words[length + len(on_board)].add(word)
