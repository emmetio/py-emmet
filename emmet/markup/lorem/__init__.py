import re
from random import randint
from ...abbreviation import AbbreviationNode
from ...config import Config
from ..implicit_tag import resolve_implicit_tag
from .latin import vocabulary as latin
from .russian import vocabulary as ru
from .spanish import vocabulary as sp

re_lorem = re.compile(r'^lorem([a-z]*)(\d*)(-\d*)?$', re.I)

vocabularies = {
    'ru': ru,
    'sp': sp,
    'latin': latin
}

def lorem(node: AbbreviationNode, ancestors: list, config: Config):
    if not node.name:
        return

    m = re_lorem.match(node.name)
    if m:
        db = vocabularies.get(m.group(1)) or vocabularies.get('latin')
        min_word_count = max(1, int(m.group(2))) if m.group(2) else 30
        max_word_count = max(min_word_count, int(m.group(3)[1:])) if m.group(3) else min_word_count
        word_count = randint(min_word_count, max_word_count)
        repeat = node.repeat or find_repeater(ancestors)

        node.name = node.attributes = None
        node.value = [paragraph(db, word_count, not repeat or repeat.value == 0)]

        if node.repeat and len(ancestors) > 1:
            resolve_implicit_tag(node, ancestors, config)

def sample(arr: list, count: int):
    l = len(arr)
    iterations = min(l, count)
    result = []

    while len(result) < iterations:
        item = arr[randint(0, l - 1)]
        if item not in result:
            result.append(item)

    return result


def choice(val: str):
    return val[randint(0, len(val) - 1)]


def sentence(words: list, end: str=None):
    if words:
        words = [words[0].capitalize()] + words[1:]

    return ' '.join(words) + (end or choice('?!...')) # more dots than question marks

def insert_commas(words: list):
    """
    Insert commas at randomly selected words. This function modifies values
    inside `words` array
    """
    if len(words) < 2:
        return words

    words = words[:]
    l = len(words)
    total_commas = 0

    if 3 < l <= 6:
        total_commas = randint(0, 1)
    elif 6 < l <= 12:
        total_commas = randint(0, 2)
    else:
        total_commas = randint(1, 4)

    for _ in range(total_commas):
        pos = randint(0, l - 2)
        if words[pos][-1] != ',':
            words[pos] += ','

    return words

def paragraph(db: dict, word_count: int, start_with_common=False):
    """
    Generate a paragraph of "Lorem ipsum" text
    :param db Words dictionary
    :param word_count Words count in paragraph
    :param start_with_common Should paragraph start with common "lorem ipsum" sentence.
    """
    result = []
    total_words = 0

    if start_with_common and 'common' in db:
        words = db['common'][0:word_count]
        total_words += len(words)
        result.append(sentence(insert_commas(words), '.'))

    while total_words < word_count:
        words = sample(db['words'], min(randint(2, 30), word_count - total_words))
        total_words += len(words)
        result.append(sentence(insert_commas(words)))

    return ' '.join(result)


def find_repeater(ancestors: list):
    i = len(ancestors) - 1
    while i >= 0:
        element = ancestors[i]
        if isinstance(element, AbbreviationNode) and element.repeat:
            return element.repeat
        i -= 1
