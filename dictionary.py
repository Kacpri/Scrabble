from itertools import permutations


def prepare_data(text):
    words = [set() for _ in range(16)]
    for word in text.split('\n'):
        words[len(word)].add(word)
    return words


def words_reader(file_name):
    file = open(file_name, "r", encoding='utf-8')
    file_content = file.read()
    words = prepare_data(file_content)
    file.close()
    return words


words = words_reader('slowa.txt')


def find_words(rack):
    words = [set() for _ in range(len(rack) + 1)]
    for length in range(len(rack) + 1):
        words[length] = [''.join(p) for p in set(permutations(rack, length))]
        words[length] = [word for word in words[length] if word in words[length]]
    print(words)


def check_word(word):
    word = word.lower()
    return word in words[len(word)]
