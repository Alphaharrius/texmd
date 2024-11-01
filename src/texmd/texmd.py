from pylatexenc.latexwalker import ( 
    LatexWalker,
    LatexNode,
    LatexEnvironmentNode, 
    LatexGroupNode,
    LatexMacroNode, 
    LatexCharsNode, 
    LatexMathNode,
    LatexSpecialsNode)
from pylatexenc.macrospec import ParsedMacroArgs
from abc import ABC, abstractmethod
from texmd.md import (
    MdNode,
    MdDocument,
    MdHeading,
    MdSubHeading,
    MdSubSubHeading,
    MdSubSubSubHeading,
    MdBlockQuote,
    MdText,
    MdBold,
    MdMath,
    MdEquation)
from typing import Type, Tuple, List, Dict, LiteralString


class Converter(ABC):
    """ Abstract class for converting LaTeX nodes to markdown nodes. """

    @abstractmethod
    def convert(self, node: LatexNode) -> MdNode:
        """ Convert a LaTeX node to a markdown node. """
        pass


class CharsNodeConverter(Converter):
    """ A converter for LaTeX Chars nodes. """

    def convert(self, node: LatexCharsNode) -> MdNode:
        return MdText(text=node.chars)
    

class MathNodeConverter(Converter):
    """ A converter for LaTeX Math nodes. """

    def convert(self, node: LatexMathNode) -> MdNode:
        tex = "".join(n.latex_verbatim() for n in node.nodelist)
        return MdMath(tex=tex)


_SPECIALS_MAP = {
    '``': "“",
    "''": "”"}


class SpecialsNodeConverter(Converter):
    """ A converter for LaTeX Specials nodes. """

    def convert(self, node: LatexSpecialsNode) -> MdNode:
        specials = node.latex_verbatim()
        if specials in _SPECIALS_MAP:
            return MdText(text=_SPECIALS_MAP[specials])
        return MdText(text=specials)
    

class EquationEnvironmentConverter(Converter):
    """ A converter for LaTeX equation environments, if a label is present it is ignored. """

    def convert(self, node: LatexEnvironmentNode) -> MdNode:
        nodes = (n for n in node.nodelist if not (isinstance(n, LatexMacroNode) and n.macroname == 'label'))
        content = "".join(n.latex_verbatim() for n in nodes)
        return MdEquation(tex=content)
    

class AuthorNodeConverter(Converter):
    """ A converter for LaTeX author nodes. """

    def convert(self, node: LatexMacroNode) -> MdNode:
        arguments: ParsedMacroArgs = node.nodeargd
        arg_nodes = [n for n in arguments.argnlist if n is not None]
        content_node: LatexGroupNode = arg_nodes[0]
        nodes = (n for n in content_node.nodelist if not (isinstance(n, LatexMacroNode) and n.macroname == 'label'))

        content = "".join(n.latex_verbatim() for n in nodes)
        return MdText(text=f"**Author:** {content}")
    

class TitleNodeConverter(Converter):
    """ A converter for LaTeX title nodes. """

    def convert(self, node: LatexMacroNode) -> MdNode:
        arguments: ParsedMacroArgs = node.nodeargd
        arg_nodes = [n for n in arguments.argnlist if n is not None]
        content_node: LatexGroupNode = arg_nodes[0]
        nodes = (n for n in content_node.nodelist if not (isinstance(n, LatexMacroNode) and n.macroname == 'label'))

        pipeline = ((get_converter(node), node) for node in nodes)
        children = [converter.convert(node) for converter, node in pipeline if converter is not None]
        return MdHeading(children=children)
    

class AbstractNodeConverter(Converter):
    """ A converter for LaTeX abstract nodes. """

    def convert(self, node: LatexEnvironmentNode) -> MdNode:
        pipeline = ((get_converter(node), node) for node in node.nodelist)
        prefix = [MdBold(text="Abstract:"), MdText(text=" ")]
        children = prefix + [converter.convert(node) for converter, node in pipeline if converter is not None]
        return MdBlockQuote(children=children)
    

class SectionNodeConverter(Converter):
    """ A converter for LaTeX section nodes. """

    def convert(self, node: LatexMacroNode) -> MdNode:
        arguments: ParsedMacroArgs = node.nodeargd
        arg_nodes = [n for n in arguments.argnlist if n is not None]
        content_node: LatexGroupNode = arg_nodes[0]
        nodes = (n for n in content_node.nodelist if not (isinstance(n, LatexMacroNode) and n.macroname == 'label'))

        pipeline = ((get_converter(node), node) for node in nodes)
        children = [converter.convert(node) for converter, node in pipeline if converter is not None]
        return MdSubHeading(children=children)
    

class SubSectionNodeConverter(Converter):
    """ A converter for LaTeX subsection nodes. """

    def convert(self, node: LatexMacroNode) -> MdNode:
        arguments: ParsedMacroArgs = node.nodeargd
        arg_nodes = [n for n in arguments.argnlist if n is not None]
        content_node: LatexGroupNode = arg_nodes[0]
        nodes = (n for n in content_node.nodelist if not (isinstance(n, LatexMacroNode) and n.macroname == 'label'))

        pipeline = ((get_converter(node), node) for node in nodes)
        children = [converter.convert(node) for converter, node in pipeline if converter is not None]
        return MdSubSubHeading(children=children)
    

class SubSubSectionNodeConverter(Converter):
    """ A converter for LaTeX subsubsection nodes. """

    def convert(self, node: LatexMacroNode) -> MdNode:
        arguments: ParsedMacroArgs = node.nodeargd
        arg_nodes = [n for n in arguments.argnlist if n is not None]
        content_node: LatexGroupNode = arg_nodes[0]
        nodes = (n for n in content_node.nodelist if not (isinstance(n, LatexMacroNode) and n.macroname == 'label'))

        pipeline = ((get_converter(node), node) for node in nodes)
        children = [converter.convert(node) for converter, node in pipeline if converter is not None]
        return MdSubSubSubHeading(children=children)
    

class AppendixNodeConverter(Converter):
    """ A converter for LaTeX appendix nodes. """

    def convert(self, node: LatexMacroNode) -> MdNode:
        return MdHeading(children=[MdText(text="Appendix")])
    

_LatexNodeType = Tuple[Type[LatexNode], LiteralString]


def _get_node_type(node: LatexNode) -> _LatexNodeType:
    if isinstance(node, LatexEnvironmentNode):
        return (LatexEnvironmentNode, node.environmentname)
    if isinstance(node, LatexMacroNode):
        return (LatexMacroNode, node.macroname)
    return (type(node), '')


EQN_CONVERTER = EquationEnvironmentConverter()


_CONVERTER: Dict[_LatexNodeType, Converter] = {
    (LatexCharsNode, ''): CharsNodeConverter(),
    (LatexMathNode, ''): MathNodeConverter(),
    (LatexSpecialsNode, ''): SpecialsNodeConverter(),

    (LatexMacroNode, 'author'): AuthorNodeConverter(),
    (LatexMacroNode, 'title'): TitleNodeConverter(),
    (LatexMacroNode, 'section'): SectionNodeConverter(),
    (LatexMacroNode, 'subsection'): SubSectionNodeConverter(),
    (LatexMacroNode, 'subsubsection'): SubSubSectionNodeConverter(),
    (LatexMacroNode, 'appendix'): AppendixNodeConverter(),

    (LatexEnvironmentNode, 'abstract'): AbstractNodeConverter(),
    (LatexEnvironmentNode, 'equation'): EQN_CONVERTER,
    (LatexEnvironmentNode, 'align'): EQN_CONVERTER,
    (LatexEnvironmentNode, 'equation*'): EQN_CONVERTER,
    (LatexEnvironmentNode, 'align*'): EQN_CONVERTER,
    (LatexEnvironmentNode, 'array'): EQN_CONVERTER,
    (LatexEnvironmentNode, 'eqnarray'): EQN_CONVERTER,
    (LatexEnvironmentNode, 'multline'): EQN_CONVERTER}


def get_converter(node: LatexNode) -> Converter:
    """ Get the converter for a LaTeX node. """
    node_type = _get_node_type(node)
    if node_type not in _CONVERTER:
        return None
    return _CONVERTER[node_type]


def add_converter(node_type: Type[LatexNode], node_name: LiteralString, converter: Converter):
    """
    Add a converter for a LaTeX node type and name.
    
    :param node_type: The type of the LaTeX node.
    :param node_name: The name of the LaTeX node, it is required for `LatexMacroNode` and `LatexEnvironmentNode`.
    :param converter: The converter for the LaTeX node.
    """
    _CONVERTER[(node_type, node_name)] = converter


class TexDocument:
    """ A LaTeX document. """

    def __init__(self, nodes: List[LatexNode]):
        self.nodes = nodes

    def to_md(self) -> MdDocument:
        """ Convert the document to a markdown document, skipping unsupported nodes. """
        pipeline = ((get_converter(node), node) for node in self.nodes)
        children = [converter.convert(node) for converter, node in pipeline if converter is not None]
        return MdDocument(children=children)
    

def set_bib_converter(converter: Converter):
    """
    Set the converter for LaTeX bibliography nodes.
    
    :param converter: The converter for LaTeX bibliography nodes, if there are no bib information
    for the current context set this to `None`.
    """
    add_converter(LatexMacroNode, 'cite', converter)


def load_file(path: str) -> TexDocument:
    """
    Load a LaTeX document from a file.
    
    :param path: The path to the LaTeX file.
    """
    with open(path, 'r') as file:
        content = file.read()
    w = LatexWalker(content)
    nodes, _, _ = w.get_latex_nodes()
    doc_nodes = [n for n in nodes if isinstance(n, LatexEnvironmentNode)]
    if len(doc_nodes) > 1:
        raise ValueError("Multiple documents in a single file are not supported.")
    return TexDocument(nodes=doc_nodes[0].nodelist)


def parse(tex: str) -> TexDocument:
    """
    Get a LaTeX document from a TeX string.
    
    :param tex: The TeX string.
    """
    w = LatexWalker(tex)
    nodes, _, _ = w.get_latex_nodes()
    return TexDocument(nodes=nodes)
