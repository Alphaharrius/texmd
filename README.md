# texmd
A small library that converts LaTeX to Markdown.

## Usage
This package allows you to load a `.tex` file directly.
```python
from texmd import texmd # Import the package

file_path = "<PATH_TO_TEX_FILE>"
tex_file = texmd.load_file(file_path)
```
The loaded file ```tex_file``` is type of ```texmd.texmd.TexDocument```.

If you want to parse the LaTeX string directly you can also do
```python
tex_expr = "<TEX_EXPR>"
tex_file = texmd.parse(tex_expr)
```

We can convert then it to Markdown by
```python
document = tex_file.to_md()
```
The output `document` is type of ```texmd.md.MdDocument```.
To output the `document` as Markdown syntax we can do
```python
md = document.to_str()
```
and you can write it to a `.md` file.
