def calculate_score(abbr: str, text: str):
    """
    Calculates fuzzy match score of how close `abbr` matches given `string`.
    :param abbr Abbreviation to score
    :param str String to match
    :return Match score
    """
    abbr = abbr.lower()
    text = text.lower()

    if abbr == text:
        return 1

    # a string MUST start with the same character as abbreviation
    if not text or abbr[0] != text[0]:
        return 0

    abbr_length = len(abbr)
    string_length = len(text)
    i = 1
    j = 1
    score = string_length

    while i < abbr_length:
        ch1 = abbr[i]
        found = False
        acronym = False

        while j < string_length:
            ch2 = text[j]

            if ch1 == ch2:
                found = True
                score += (string_length - j) * (2 if acronym else 1)
                break

            # add acronym bonus for exactly next match after unmatched `-`
            acronym = ch2 == '-'
            j += 1

        if not found:
            break

        i += 1

    return score * (i / abbr_length) / n_sum(string_length)


def n_sum(n: int):
    "Calculates sum of first `n` numbers, e.g. 1+2+3+...n"
    return n * (n + 1) / 2
