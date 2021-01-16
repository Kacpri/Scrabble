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


class Dictionary:
    words = words_reader('slowa.txt')
    pairs = words_reader('dwojki.txt')
    threes = words_reader('trojki.txt')

    def __init__(self):
        print()




