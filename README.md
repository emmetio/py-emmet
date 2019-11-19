# Emmet — the essential toolkit for web-developers

> This is the official Python port of original Emmet code base written in JavaScript: https://github.com/emmetio/emmet

Emmet is a web-developer’s toolkit for boosting HTML & CSS code writing.

With Emmet, you can type expressions (_abbreviations_) similar to CSS selectors and convert them into code fragment with a single keystroke. For example, this abbreviation:

```
ul#nav>li.item$*4>a{Item $}
```

...can be expanded into:

```html
<ul id="nav">
    <li class="item1"><a href="">Item 1</a></li>
    <li class="item2"><a href="">Item 2</a></li>
    <li class="item3"><a href="">Item 3</a></li>
    <li class="item4"><a href="">Item 4</a></li>
</ul>
```

## Features

* **Familiar syntax**: as a web-developer, you already know how to use Emmet. Abbreviation syntax is similar to CSS Selectors with shortcuts for id, class, custom attributes, element nesting and so on.
* **Dynamic snippets**: unlike default editor snippets, Emmet abbreviations are dynamic and parsed as-you-type. No need to predefine them for each project, just type `MyComponent>custom-element` to convert any word into a tag.
* **CSS properties shortcuts**: Emmet provides special syntax for CSS properties with embedded values. For example, `bd1-s#f.5` will be exampled to `border: 1px solid rgba(255, 255, 255, 0.5)`.
* **Available for most popular syntaxes**: use single abbreviation to produce code for most popular syntaxes like HAML, Pug, JSX, SCSS, SASS etc.

[Read more about Emmet features](https://docs.emmet.io)

### Installation

You can install Emmet as a regular pip module:

```bash
pip install py-emmet
```

## Usage

To expand abbreviation, pass it to `expand` function of `emmet` module:

```py
import emmet

print(emmet.expand('p>a')) # <p><a href=""></a></p>
```

By default, Emmet expands *markup* abbreviation, e.g. abbreviation used for producing nested elements with attributes (like HTML, XML, HAML etc.). If you want to expand *stylesheet* abbreviation, you should pass it as a `type` property of second argument:

```py
import emmet

print(emmet.expand('p10', { 'type': 'stylesheet' })) # padding: 10px
```

A stylesheet abbreviation has slightly different syntax compared to markup one: it doesn’t support nesting and attributes but allows embedded values in element name.

Alternatively, Emmet supports *syntaxes* with predefined snippets and options:

```py
import emmet

print(emmet.expand('p10', { 'syntax': 'css' })) # padding: 10px;
print(emmet.expand('p10', { 'syntax': 'stylus' })) # padding 10px
```

Predefined syntaxes already have `type` attribute which describes whether given abbreviation is markup or stylesheet, but if you want to use it with your custom syntax name, you should provide `type` config option as well (default is `markup`):

```py
import emmet

print(emmet.expand('p10', {
    'syntax': 'my-custom-syntax',
    'type': 'stylesheet',
    'options': {
        'stylesheet.between': '__',
        'stylesheet.after': '',
    }
})) # padding__10px
```

You can pass `options` property as well to shape-up final output or enable/disable various features. See [`emmet/config.py`](emmet/config.py) for more info and available options.

## Extracting abbreviations from text

A common workflow with Emmet is to type abbreviation somewhere in source code and then expand it with editor action. To support such workflow, abbreviations must be properly _extracted_ from source code:

```py
import emmet

source = 'Hello world ul.tabs>li'
data = emmet.extract(source, 22) # { abbreviation: 'ul.tabs>li' }

print(emmet.expand(data.abbreviation)) # <ul class="tabs"><li></li></ul>
```

The `extract` function accepts source code (most likely, current line) and character location in source from which abbreviation search should be started. The abbreviation is searched in backward direction: the location pointer is moved backward until it finds abbreviation bound. Returned result is an object with `abbreviation` property and `start` and `end` properties which describe location of extracted abbreviation in given source.

Most current editors automatically insert closing quote or bracket for `(`, `[` and `{` characters so when user types abbreviation that uses attributes or text, it will end with the following state (`|` is caret location):

```
ul>li[title="Foo|"]
```

E.g. caret location is not at the end of abbreviation and must be moved a few characters ahead. The `extract` function is able to handle such cases with `lookAhead` option (enabled by default). This this option enabled, `extract` method automatically detects auto-inserted characters and adjusts location, which will be available as `end` property of the returned result:

```py
import emmet

source = 'a div[title] b'
loc = 11 # right after "title" word

# `lookAhead` is enabled by default
print(emmet.extract(source, loc)) # { abbreviation: 'div[title]', start: 2, end: 12 }
print(emmet.extract(source, loc, { 'lookAhead': false })) # { abbreviation: 'title', start: 6, end: 11 }
```

By default, `extract` tries to detect _markup_ abbreviations (see above). _stylesheet_ abbreviations has slightly different syntax so in order to extract abbreviations for stylesheet syntaxes like CSS, you should pass `type: 'stylesheet'` option:

```py
import emmet

source = 'a{b}'
loc = 3 # right after "b"

print(emmet.extract(source, loc)); # { abbreviation: 'a{b}', start: 0, end: 4 }


# Stylesheet abbreviations does not have `{text}` syntax
print(emmet.extract(source, loc, { 'type': 'stylesheet' })); # { abbreviation: 'b', start: 2, end: 3 }
```

### Extract abbreviation with custom prefix

Lots of developers uses React (or similar) library for writing UI code which mixes JS and XML (JSX) in the same source code. Since _any_ Latin word can be used as Emmet abbreviation, writing JSX code with Emmet becomes pain since it will interfere with native editor snippets and distract user with false positive abbreviation matches for variable names, methods etc.:

```js
var div // `div` is a valid abbreviation, Emmet may transform it to `<div></div>`
```

A possible solution for this problem it to use _prefix_ for abbreviation: abbreviation can be successfully extracted only if its preceded with given prefix.

```py
import emmet

source1 = '() => div'
source2 = '() => <div'

emmet.extract(source1, len(source1)) # Finds `div` abbreviation
emmet.extract(source2, len(source2)) # Finds `div` abbreviation too

emmet.extract(source1, len(source1), { 'prefix': '<' }) # No match, `div` abbreviation is not preceded with `<` prefix
emmet.extract(source2, len(source2), { 'prefix': '<' }) # Finds `div` since it preceded with `<` prefix
```

With `prefix` option, you can customize your experience with Emmet in any common syntax (HTML, CSS and so on) if user is distracted too much with Emmet completions for any typed word. A `prefix` may contain multiple character but the last one *must* be a character which is not part of Emmet abbreviation. Good candidates are `<`, `&`, `→` (emoji or Unicode symbol) and so on.
