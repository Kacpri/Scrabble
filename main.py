from sack import Sack
from itertools import permutations
import re
from collections import Counter
import time


# import sys
# from PySide6.QtUiTools import QUiLoader
# from PySide6.QtWidgets import QApplication
# from PySide6.QtCore import QFile, QIODevice


def find_words(rack, dictionary):
    words = [set() for _ in range(len(rack) + 1)]
    for length in range(len(rack) + 1):
        words[length] = [''.join(p) for p in set(permutations(rack, length))]
        words[length] = [word for word in words[length] if word in dictionary[length]]
    print(words)


def find_words_with_letters_on_board(rack, dictionary, letters, max_letters_before, max_letters_after):
    words = [set() for _ in range(len(rack) + len(letters) + 1)]
    pattern = re.compile(rf'^.{{0,{max_letters_before}}}{letters}.{{0,{max_letters_after}}}$')
    for length in range(len(rack) + len(letters) + 1):
        words[length] = [''.join(p) for p in set(permutations(rack + letters, length))]
        words[length] = [word for word in words[length] if word in dictionary[length] and re.match(pattern, word)]
    print(words)


def find_words_with_bridge(rack, dictionary, first, second, max_letters_before, max_letters_between, max_letters_after):
    words = [set() for _ in range(len(rack) + len(first) + len(second) + 1)]
    pattern = re.compile(
        rf'^.{{0,{max_letters_before}}}{first}.{{0,{max_letters_after}}}{second}.{{0,{max_letters_after}}}$')
    for length in range(len(rack) + len(first) + len(second) + 1):
        words[length] = [''.join(p) for p in set(permutations(rack + first + second, length))]
        words[length] = [word for word in words[length] if word in dictionary[length] and re.match(pattern, word)]
    print(words)


def prepare_dictionary(dictionary):
    words = [set() for _ in range(16)]
    for word in dictionary.split('\n'):
        words[len(word)].add(word)
    return words


def find_groups(dictionary, length, file_name):
    groups = []
    for word in dictionary.split('\n'):
        for i in range(len(word) + 1 - length):
            group = word[i:i + length]
            if not any(letter in group for letter in ['v', 'x', 'q']):
                groups.append(word[i:i + 2])




def find_trios(dictionary):
    trios = []
    for word in dictionary.split('\n'):
        for i in range(len(word) - 2):
            trios.append(word[i:i + 3])



def main():
    file = open("slowa.txt", "r", encoding='utf-8')
    whole_dictionary = file.read()
    file.close()
    dictionary = prepare_dictionary(whole_dictionary)

    pairs = find_pairs(whole_dictionary)
    # for word in dictionary[2]:
    #     if word not in pairs:
    #         print(word)
    print(pairs)
    trios = find_trios(whole_dictionary)
    print(trios)


    # ui_file_name = "board.ui"
    # ui_file = QFile(ui_file_name)
    # if not ui_file.open(QIODevice.ReadOnly):
    #     print("Cannot open {}: {}".format(ui_file_name, ui_file.errorString()))
    #     sys.exit(-1)
    # loader = QUiLoader()
    # window = loader.load(ui_file)
    # ui_file.close()
    # if not window:
    #     print(loader.errorString())
    #     sys.exit(-1)
    # window.show()

    sack = Sack()
    rack = sack.draw(7)
    print(rack)
    find_words(rack, dictionary)
    find_words_with_letters_on_board(rack, dictionary, 'as', 2, 3)
    find_words_with_bridge(rack, dictionary, 'a', 'e', 8, 3, 3)


if __name__ == '__main__':
    main()
