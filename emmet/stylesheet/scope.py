class CSSAbbreviationScope:
    Global = '@@global'
    "Include all possible snippets in match"

    Section = '@@section'
    "Include raw snippets only (e.g. no properties) in abbreviation match"

    Property = '@@property'
    "Include properties only in abbreviation match"

    Value = '@@value'
    "Resolve abbreviation in context of CSS property value"
