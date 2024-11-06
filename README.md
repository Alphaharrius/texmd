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
