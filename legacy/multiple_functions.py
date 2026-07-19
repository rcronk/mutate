import string

def count_words(text):
    return len(text.split())

def count_letters(text):
    return len([x for x in text if x in string.ascii_letters])

def count_spaces(text):
    return len([x for x in text if x == ' '])

def get_stats(text):
    stats = {}
    stats['words'] = count_words(text)
    stats['letters'] = count_letters(text)
    stats['spaces'] = count_spaces(text)
    return stats