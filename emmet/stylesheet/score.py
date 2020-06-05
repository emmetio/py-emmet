def calculate_score(str1: str, str2: str, partial_match=False):
    """
    Calculates how close `str1` matches `str2` using fuzzy match.
    How matching works:
    – first characters of both `str1` and `str2` *must* match
    – `str1` length larger than `str2` length is allowed only when `unmatched` is true
    – ideal match is when `str1` equals to `str2` (score: 1)
    – next best match is `str2` starts with `str1` (score: 1 × percent of matched characters)
    – other scores depend on how close characters of `str1` to the beginning of `str2`
    :param partial_match Allow length `str1` to be greater than `str2` length
    """
    str1 = str1.lower()
    str2 = str2.lower()

    if str1 == str2:
        return 1

    # Both strings MUST start with the same character
    if not str1 or not str2 or str1[0] != str2[0]:
        return 0

    str1_len = len(str1)
    str2_len = len(str2)

    if not partial_match and str1_len > str2_len:
        return 0

    # Characters from `str1` which are closer to the beginning of a `str2` should
    # have higher score.
    # For example, if `str2` is `abcde`, it’s max score is:
    # 5 + 4 + 3 + 2 + 1 = 15 (sum of character positions in reverse order)
    # Matching `abd` against `abcde` should produce:
    # 5 + 4 + 2 = 11
    # Acronym bonus for match right after `-`. Matching `abd` against `abc-de`
    # should produce:
    # 6 + 5 + 4 (use `d` position in `abd`, not in abc-de`)

    min_length = min(str1_len, str2_len)
    max_length = max(str1_len, str2_len)
    i = 1
    j = 1
    score = max_length
    found = False
    acronym = False

    while i < str1_len:
        ch1 = str1[i]
        found = False
        acronym = False

        while j < str2_len:
            ch2 = str2[j]

            if ch1 == ch2:
                found = True
                score += max_length - (i if acronym else j)
                break

            # add acronym bonus for exactly next match after unmatched `-`
            acronym = ch2 == '-'
            j += 1


        if not found:
            if not partial_match:
                return 0
            break

        i += 1

    match_ratio = i / max_length
    delta = max_length - min_length
    max_score = n_sum(max_length) - n_sum(delta)
    return (score * match_ratio) / max_score


def n_sum(n: int):
    "Calculates sum of first `n` numbers, e.g. 1+2+3+...n"
    return n * (n + 1) / 2
