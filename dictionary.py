from itertools import permutations
from sack import Sack


def prepare_data(text):
    words = [set() for _ in range(16)]
    for word in text.split('\n'):
        words[len(word)].add(word)
    return words


def words_reader(file_name):
    file = open(file_name, "r", encoding='utf-8')
    file_content = file.read()
    file.close()
    return file_content


data = words_reader('slowa.txt')
dictionary = prepare_data(data)
data = words_reader('czworki.txt')
quads = []
for quad in data.split('\n'):
    quads.append(quad)


def is_word_in_dictionary(word):
    word = word.lower()
    if '_' in word:
        for letter in Sack.values_without_blank():
            letter = letter.lower()
            new_word = word.replace("_", letter, 1)
            if '_' in new_word:
                if is_word_in_dictionary(new_word):
                    return True
            elif new_word in dictionary[len(word)]:
                return True
    if word in dictionary[len(word)]:
        return True
    return False


def is_in_quads(word):
    return word.lower() in quads


def possible_words_with_blank(word, find_letters=False):
    word = word.lower()
    if '_' not in word:
        return word
    words = []
    for letter in Sack.values_without_blank():
        letter = letter.lower()
        new_word = word.replace("_", letter, 1)
        if '_' in new_word:
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
    print(words)


def find_groups(length):
    groups = set()
    for words_by_length in dictionary:
        for word in words_by_length:
            for i in range(len(word) + 1 - length):
                group = word[i:i + length]
                if not any(letter in group for letter in ['v', 'x', 'q']):
                    groups.add(group)
    return groups


def install():
    filenames = ["trojki.txt", "czworki.txt", "piatki.txt", "szostki.txt", "siodemki.txt"]
    for count in range(5):
        file = open(filenames[count], "w", encoding='utf-8')
        groups = find_groups(count + 3)
        for group in sorted(groups):
            file.write(f'{group}\n')


if __name__ == '__main__':
    install()