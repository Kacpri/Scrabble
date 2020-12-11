from sack import Sack
from itertools import permutations
import re


def find_words_with_letters_on_board(rack, dictionary, letters, max_letters_before, max_letters_after):
    words = [set() for _ in range(len(rack) + len(letters) + 1)]
    pattern = re.compile(rf'^.{{0,{max_letters_before}}}{letters}.{{0,{max_letters_after}}}$')
    for length in range(len(rack) + len(letters) + 1):
        words[length] = [''.join(p) for p in set(permutations(rack + letters, length))]
        words[length] = [word for word in words[length] if word in dictionary[length] and re.match(pattern, word)]
    print(words)


def find_words_from_letters(rack, dictionary):
    words = [set() for _ in range(len(rack) + 1)]
    for length in range(len(rack) + 1):
        words[length] = [''.join(p) for p in set(permutations(rack, length))]
        words[length] = [word for word in words[length] if word in dictionary[length]]
    print(words)


def prepare_dictionary(dictionary):
    words = [set() for _ in range(16)]
    for word in dictionary.split('\n'):
        words[len(word)].add(word)
    return words


def main():
    file = open("slowa.txt", "r", encoding='utf-8')
    dictionary = file.read()
    file.close()
    dictionary = prepare_dictionary(dictionary)

    sack = Sack()
    rack = sack.draw(7)
    print(rack)
    find_words_from_letters(rack, dictionary)
    find_words_with_letters_on_board(rack, dictionary, 'as', 2, 3)


if __name__ == '__main__':
    main()
