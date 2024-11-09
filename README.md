# texmd
A small library that converts LaTeX to Markdown.
This package uses `pylatexenc` to parse the LaTeX expressions.

Currently, it supports converting inlined mathematical equations `$...$`, 
equation blocks (`equation`, `equation*`, `align`, `align*`, `array`, `matrix`, `eqnarray`, `multline`), 
title `\title`, sections (`\section`, `\subsection`, `subsubsection`); abstract content `\abstract{...}` 
(supported by Markdown block quote); in-text quotations ``` ``...'' ```; equation numbered labels are also supported.
More will be introduced in later versions.

## Installation
Run ```pip install texmd``` in the terminal.

## Usage
This package allows you to load a `.tex` file directly.
```python
from texmd import tex # Import the package

parser = tex.TexParser()
file_path = "<PATH_TO_TEX_FILE>"
tex_file = parser.load_file(file_path) # Load the file
```
The loaded file ```tex_file``` is type of ```texmd.texmd.TexDocument```.

If you want to parse the LaTeX string directly you can also do
```python
tex_expr = "<TEX_EXPR>"
tex_file = parser.parse(tex_expr)
```

We can convert then it to Markdown by
```python
document = parser.to_md(tex_file)
```
The output `document` is type of ```texmd.md.MdDocument```.
To output the `document` as Markdown syntax we can do
```python
md = document.to_str()
```
and you can write it to a `.md` file.

## Add BibTeX support
In order for the package to also process BibTeX we will have to load the `.bib` file.
```python
parser.load_citations("<BIB_FILE_PATH>")
```

## Customization
If you don't like the way the package write the Markdown, or you want to support custom LaTeX expressions,
you can use the API ```parser.set_converter``` with a specific sub-type of `texmd.tex.TexNode`.

For example you want to set a new converter for text node.
```python
class TextNodeConverter(Converter):
    """ A converter for LaTeX text nodes. """

    def __init__(self):
        super().__init__(None)

    def convert(self, node: TexTextNode) -> Generator[MdNode]:
        def _():
            yield MdText(text=node.text)
        return _()

converter = TextNodeConverter()
parser.set_converter(TexTextNode, '', converter)
```

The default Citation converter is implemented as follows,
```python
class CiteConverter(Converter):
    """ A converter for LaTeX cite nodes. """

    def __init__(self, parser: 'TexParser'):
        super().__init__(parser)

    def convert(self, node: TexMacroNode) -> Generator[MdNode]:
        def write_author(author: bib.Author) -> str:
            first_abbr = author.first_name[0] + '.' if author.first_name else ''
            middle_abbr = author.middle_name[0] + '.' if author.middle_name else ''
            return f"{first_abbr} {middle_abbr} {author.last_name}"
        
        def write_entry(entry: bib.Entry) -> str:
            content: List[str] = [*(write_author(author) for author in entry.authors), entry.title, entry.year]
            return ", ".join(content)

        def _():
            chars: TexTextNode = node.children[0].children[0]
            cite_names = chars.text.replace(' ', '').split(',')
            citations = (self.parser._get_citation(name) for name in cite_names)
            citations = (write_entry(entry) for entry in citations if entry)
            yield MdText(text="(*" + ", ".join(citations) + "*)")
        return _()
```
If you want a different style you can implement a new one and load it via
```python
class YourCiteConverter(Converter)
    ...

converter = YourCiteConverter(parser)
parser.set_converter(TexMacroNode, 'cite', converter)
```
And you can obtain the citation entries via ```texmd.tex.TexParser._get_citation```
in the format of ```texmd.bib.Entry```.
