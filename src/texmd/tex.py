from pylatexenc.latexwalker import (
    LatexWalker,
    LatexNode,
    LatexEnvironmentNode, 
    LatexGroupNode,
    LatexMacroNode, 
    LatexCharsNode, 
    LatexMathNode,
    LatexCommentNode,
    LatexSpecialsNode)
from pydantic import BaseModel
from typing import Type, Generator, Tuple, List, Dict
from multipledispatch import dispatch
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


class TexNode(BaseModel, ABC):
    """ Base class for LaTeX nodes. """
    
    @abstractmethod
    def __str__(self) -> str:
        """ Convert the node to a markdown string. """
        pass

    @abstractmethod
    def get_node_type(self) -> '__ConverterEntry':
        pass


class TexParentNode(TexNode, ABC):
    """ A LaTeX group node containing children nodes. """

    children: List[TexNode]
    """ The children nodes of the group. """

    prefix: str
    """ The prefix of the group. """

    suffix: str
    """ The suffix of the group. """

    def find(self, type: Type[TexNode] = None, name: str = "", deep: bool = False) -> List[TexNode]:
        """
        Find children nodes from the group by their type and name. The parameters `type` and `name` are used to
        identify the children nodes to be found, if both are provided the children nodes must be of the specified 
        type and name.

        :param type: The type of the children nodes to be found.
        :param name: The name of the `TexNamedNode` children nodes to be found.
        :param deep: Whether to perform the search for the whole node tree.

        :return: The list of children nodes found.
        """
        ret = []
        for child in self.children:
            type_and_name: bool = (
                type and name and 
                isinstance(child, type) and isinstance(child, TexNamedNode) and child.name == name)
            type_only: bool = type and not name and isinstance(child, type)
            name_only: bool = not type and name and isinstance(child, TexNamedNode) and child.name == name
            if type_and_name or type_only or name_only: ret.append(child)
            if deep and isinstance(child, TexParentNode): ret.extend(child.find(type, name, deep=deep))

        return ret

    def remove(self, type: Type[TexNode] = None, name: str = "", deep: bool = False) -> None:
        """
        Remove children nodes from the group by their type and name. The parameters `type` and `name` are used to
        identify the children nodes to be removed, if both are provided the children nodes must be of the specified 
        type and name. If `deep` is `True` the method will also perform the removal for the whole node tree.

        :param type: The type of the children nodes to be removed.
        :param name: The name of the `TexNamedNode` children nodes to be removed.
        :param deep: Whether to perform the removal for the whole node tree.
        """
        for child in self.children:
            type_and_name: bool = (
                type and name and 
                isinstance(child, type) and isinstance(child, TexNamedNode) and child.name == name)
            type_only: bool = type and not name and isinstance(child, type)
            name_only: bool = not type and name and isinstance(child, TexNamedNode) and child.name == name
            if type_and_name or type_only or name_only: self.children.remove(child); continue
            if deep and isinstance(child, TexParentNode): child.remove(type, name, deep=deep)

    def group_latex(self) -> str:
        """ Get the LaTeX expression inside the group. """
        return ''.join(str(n) for n in self.children)


class TexNamedNode(TexNode, ABC):
    """ A LaTeX node with a name. """

    name: str
    """ The name of the node. """


ALLOWED_GROUP_DECO = set(['topic'])
""" Allowed group decorators like `{\\topic ...}`. """


class TexGroupNode(TexParentNode):
    """ A LaTeX group node. """

    def __str__(self):
        return self.prefix + self.group_latex() + self.suffix
    
    def get_decorators(self) -> List['TexMacroNode']:
        """ Get the decorators of the group. """
        ret = [n for n in self.find(TexMacroNode) if n.name in ALLOWED_GROUP_DECO]
        ret.sort(key=lambda x: x.name)
        return ret

    def get_node_type(self):
        """ Get the type of the node, this is used to identify the converter for the node. """
        decos = self.get_decorators()
        deco_names = ':'.join(macro.name for macro in decos)
        return (TexGroupNode, deco_names)


class TexMacroNode(TexNamedNode, TexParentNode):
    """ A LaTeX macro node. """

    def __str__(self):
        return f'\\{self.name}' + self.group_latex()

    def get_node_type(self):
        return (TexMacroNode, self.name)


class TexEnvNode(TexNamedNode, TexParentNode):
    """ A LaTeX environment node. """

    def __str__(self):
        return (f'\\begin{{{self.name}}}' + 
                self.group_latex() + f'\\end{{{self.name}}}')

    def get_node_type(self):
        return (TexEnvNode, self.name)


class TexTextNode(TexNode):
    """ A LaTeX text node. """

    text: str
    """ The text of the node. """

    def __str__(self):
        return self.text

    def get_node_type(self):
        return (TexTextNode, '')


class TexSpecialsNode(TexTextNode):
    """ A LaTeX specials node. """

    def __str__(self):
        return self.text

    def get_node_type(self):
        return (TexSpecialsNode, '')


class TexMathNode(TexParentNode):
    """ A LaTeX math node. """

    def __str__(self):
        return self.prefix + self.group_latex() + self.suffix

    def get_node_type(self):
        return (TexMathNode, '')


class TexDocNode(TexEnvNode):
    """ A LaTeX document. """


def convert(node: LatexNode) -> None:
    raise NotImplementedError(f"Conversion not implemented for {type(node)}.")


@dispatch(LatexGroupNode)
def convert(node: LatexGroupNode) -> List[TexNode]:
    ret = TexGroupNode(
        children=[v for n in node.nodelist for v in convert(n)],
        group_latex_expr=''.join(n.latex_verbatim() for n in node.nodelist),
        prefix=node.delimiters[0],
        suffix=node.delimiters[1])
    return [ret]


@dispatch(LatexMacroNode)
def convert(node: LatexMacroNode) -> List[TexNode]:
    arguments = [n for n in node.nodeargd.argnlist if n] if node.nodeargd else []
    children = [
        v if isinstance(v, TexGroupNode) 
        else TexGroupNode(children=[v], group_latex_expr=str(v), prefix='{', suffix='}') 
        for n in arguments for v in convert(n)]
    suffix_nodes = (
        [TexTextNode(text=node.macro_post_space)] 
        if node.macro_post_space else [])
    macro_node = TexMacroNode(
        name=node.macroname,
        children=children,
        group_latex_expr=''.join(n.latex_verbatim() for n in arguments),
        prefix='',
        suffix='')
    return [macro_node] + suffix_nodes


@dispatch(LatexEnvironmentNode)
def convert(node: LatexEnvironmentNode) -> List[TexNode]:
    env_args = [n for n in node.nodeargd.argnlist if n] if node.nodeargd else []
    arguments = [
        v if isinstance(v, TexGroupNode) 
        else TexGroupNode(children=[v], group_latex_expr=str(v), prefix='{', suffix='}') 
        for n in env_args for v in convert(n)]
    children = arguments + [v for n in node.nodelist for v in convert(n)]
    ret = TexEnvNode(
        name=node.environmentname,
        children=children,
        group_latex_expr=''.join(str(n) for n in children),
        prefix='',
        suffix='')
    return [ret]


@dispatch(LatexCharsNode)
def convert(node: LatexCharsNode) -> List[TexNode]:
    return [TexTextNode(text=node.latex_verbatim())]


@dispatch(LatexSpecialsNode)
def convert(node: LatexSpecialsNode) -> List[TexNode]:
    return [TexSpecialsNode(text=node.latex_verbatim())]


@dispatch(LatexMathNode)
def convert(node: LatexMathNode) -> List[TexNode]:
    ret = TexMathNode(
        children=[v for n in node.nodelist for v in convert(n)],
        group_latex_expr=''.join(n.latex_verbatim() for n in node.nodelist),
        prefix=node.delimiters[0],
        suffix=node.delimiters[1])
    return [ret]


@dispatch(LatexCommentNode)
def convert(node: LatexCommentNode) -> List[TexNode]:
    return []


class Converter(ABC):
    """ Abstract class for a LaTeX to markdown converter. """

    def __init__(self, parser: 'TexParser'):
        self.parser = parser

    @abstractmethod
    def convert(self, node: TexNode) -> Generator[MdNode]:
        """
        Convert a LaTeX node to some markdown nodes.
        
        :param node: The LaTeX node to be converted.
        
        :return: The markdown nodes.
        """
        pass


class GroupNodeConverter(Converter):
    """ A converter for LaTeX group nodes. """

    def __init__(self, parser: 'TexParser'):
        super().__init__(parser)

    def convert(self, node: TexGroupNode) -> Generator[MdNode]:
        def _():
            yield MdText(text=node.prefix)
            pipeline = ((self.parser.get_converter(child), child) for child in node.children)
            for converter, child in pipeline:
                if converter is not None:
                    for v in converter.convert(child):
                        yield v
            yield MdText(text=node.suffix)
        return _()


class TextNodeConverter(Converter):
    """ A converter for LaTeX text nodes. """

    def __init__(self, parser: 'TexParser'):
        super().__init__(parser)

    def convert(self, node: TexTextNode) -> Generator[MdNode]:
        def _():
            yield MdText(text=node.text)
        return _()
    

SPECIALS_MAPPING = {
    '``': "“",
    "''": "”"
}
""" Mapping of LaTeX specials to markdown specials. """


class SpecialsNodeConverter(Converter):
    """ A converter for LaTeX specials nodes. """

    def __init__(self, parser: 'TexParser'):
        super().__init__(parser)

    def convert(self, node: TexSpecialsNode) -> Generator[MdNode]:
        def _():
            yield MdText(text=SPECIALS_MAPPING.get(node.text, node.text))
        return _()
    

class MathNodeConverter(Converter):
    """ A converter for LaTeX math nodes. """

    def __init__(self, parser: 'TexParser'):
        super().__init__(parser)

    def convert(self, node: TexMathNode) -> Generator[MdNode]:
        def _():
            yield MdMath(tex=node.group_latex())
        return _()
    

class AuthorConverter(Converter):
    """ A converter for LaTeX author nodes. """

    def __init__(self, parser: 'TexParser'):
        super().__init__(parser)

    def convert(self, node: TexMacroNode) -> Generator[MdNode]:
        def _():
            group: TexGroupNode = node.children[0]
            yield MdText(text=f"**Author:** {group.group_latex()}")
        return _()
    

class TitleConverter(Converter):
    """ A converter for LaTeX title nodes. """

    def __init__(self, parser: 'TexParser'):
        super().__init__(parser)

    def convert(self, node: TexMacroNode) -> Generator[MdNode]:
        def _():
            group = node.children[0]
            pipeline = ((self.parser.get_converter(child), child) for child in group.children)
            yield MdHeading(
                children=[v for converter, n in pipeline if converter is not None for v in converter.convert(n)])
        return _()
    

class SectionConverter(Converter):
    """ A converter for LaTeX section nodes. """

    def __init__(self, parser: 'TexParser'):
        super().__init__(parser)

    def convert(self, node: TexMacroNode) -> Generator[MdNode]:
        def _():
            group = node.children[0]
            pipeline = ((self.parser.get_converter(child), child) for child in group.children)
            yield MdSubHeading(
                children=[v for converter, n in pipeline if converter is not None 
                          for v in converter.convert(n)])
        return _()
    

class SubSectionConverter(Converter):
    """ A converter for LaTeX subsection nodes. """

    def __init__(self, parser: 'TexParser'):
        super().__init__(parser)

    def convert(self, node: TexMacroNode) -> Generator[MdNode]:
        def _():
            group = node.children[0]
            pipeline = ((self.parser.get_converter(child), child) for child in group.children)
            yield MdSubSubHeading(
                children=[v for converter, n in pipeline if converter is not None 
                          for v in converter.convert(n)])
        return _()
    

class SubSubSectionConverter(Converter):
    """ A converter for LaTeX subsubsection nodes. """

    def __init__(self, parser: 'TexParser'):
        super().__init__(parser)

    def convert(self, node: TexMacroNode) -> Generator[MdNode]:
        def _():
            group = node.children[0]
            pipeline = ((self.parser.get_converter(child), child) for child in group.children)
            yield MdSubSubSubHeading(
                children=[v for converter, n in pipeline if converter is not None 
                          for v in converter.convert(n)])
        return _()
    

class AbstractConverter(Converter):
    """ A converter for LaTeX abstract nodes. """

    def __init__(self, parser: 'TexParser'):
        super().__init__(parser)

    def convert(self, node: TexEnvNode) -> Generator[MdNode]:
        def _():
            pipeline = ((self.parser.get_converter(child), child) for child in node.children)
            yield MdBlockQuote(
                children=[MdBold(text="Abstract"), MdText(text=": ")] + [
                    v for converter, child in pipeline if converter is not None 
                    for v in converter.convert(child)])
        return _()
    

class EquationConverter(Converter):
    """ A converter for LaTeX equation nodes. """

    def __init__(self, parser: 'TexParser'):
        super().__init__(parser)

    def convert(self, node: TexEnvNode) -> Generator[MdNode]:
        def _():
            # Add a star to the equation name if it does not have one,
            # this is to remove the equation numbering in the markdown.
            if not node.name.endswith('*'):
                node.name = node.name + '*'
            label = self.parser._get_ref_name(node)
            if label:
                yield MdBold(text=f"Equation ({self.parser._get_ref_id(label)})")
                yield MdText(text=":\n")
            yield MdEquation(tex=str(node))
        return _()
    

class RefConverter(Converter):
    """ A converter for LaTeX reference nodes. """

    def __init__(self, parser: 'TexParser'):
        super().__init__(parser)

    def convert(self, node: TexMacroNode) -> Generator[MdNode]:
        def _():
            label = node.children[0].children[0].text
            id = self.parser._get_ref_id(label)
            if id == -1:
                return MdText(text=f"*(Unknown reference)*")
            yield MdText(text=f"({id})")
        return _()
    

class TopicConverter(Converter):
    """ A converter for LaTeX topic nodes. """

    def __init__(self, parser: 'TexParser'):
        super().__init__(parser)

    def convert(self, node: TexMacroNode) -> Generator[MdNode]:
        def _():
            yield MdBold(text='Topic.')
        return _()


class TopicGroupConverter(Converter):
    """ A converter for LaTeX topic nodes. """

    def __init__(self, parser: 'TexParser'):
        super().__init__(parser)

    def convert(self, node: TexGroupNode) -> Generator[MdNode]:
        def _():
            pipeline = ((self.parser.get_converter(child), child) for child in node.children)
            yield MdBlockQuote(
                children=[v for converter, n in pipeline if converter is not None 
                          for v in converter.convert(n)])
        return _()


__ConverterEntry = Tuple[Type[TexNode], str]


class TexParser:
    """ A parser for LaTeX documents. """

    def __init__(self):
        self.__converters: Dict[__ConverterEntry, Converter] = {
            (TexGroupNode, ''): GroupNodeConverter(self),
            (TexTextNode, ''): TextNodeConverter(self),
            (TexSpecialsNode, ''): SpecialsNodeConverter(self),
            (TexMathNode, ''): MathNodeConverter(self),

            (TexMacroNode, 'author'): AuthorConverter(self),
            (TexMacroNode, 'title'): TitleConverter(self),
            (TexMacroNode, 'section'): SectionConverter(self),
            (TexMacroNode, 'subsection'): SubSectionConverter(self),
            (TexMacroNode, 'subsubsection'): SubSubSectionConverter(self),
            (TexMacroNode, 'topic'): TopicConverter(self),

            (TexGroupNode, 'topic'): TopicGroupConverter(self),
            (TexGroupNode, 'label:topic'): TopicGroupConverter(self),

            (TexEnvNode, 'abstract'): AbstractConverter(self),
            (TexMacroNode, 'eqref'): RefConverter(self),
            (TexMacroNode, 'ref'): RefConverter(self),

            (TexEnvNode, 'equation'): EquationConverter(self),
            (TexEnvNode, 'align'): EquationConverter(self),
            (TexEnvNode, 'array'): EquationConverter(self),
            (TexEnvNode, 'eqnarray'): EquationConverter(self),
            (TexEnvNode, 'multline'): EquationConverter(self),
            (TexEnvNode, 'matrix'): EquationConverter(self),
            (TexEnvNode, 'split'): EquationConverter(self),

            (TexEnvNode, 'equation*'): EquationConverter(self),
            (TexEnvNode, 'align*'): EquationConverter(self),
            (TexEnvNode, 'array*'): EquationConverter(self),
            (TexEnvNode, 'eqnarray*'): EquationConverter(self),
            (TexEnvNode, 'multline*'): EquationConverter(self),
            (TexEnvNode, 'matrix*'): EquationConverter(self)
        }
        self.__default_converters: Dict[Type[TexNode], Converter] = {
            TexGroupNode: GroupNodeConverter(self)
        }
        """ Mapping of LaTeX node types to their converters. """
        self.__refs: Dict[str, Tuple[int, str, TexEnvNode]] = {}
        """ Mapping of LaTeX equation labels to their ids. """
        self.__ref_names: Dict[TexEnvNode, str] = {}
        """ Mapping of LaTeX equation nodes to their labels. """

    def load_file(self, path: str) -> TexDocNode:
        """
        Load a LaTeX document from a file.
        
        :param path: The path to the LaTeX file.

        :return: The LaTeX document.
        """
        with open(path, 'r') as file:
            content = file.read()
        w = LatexWalker(content)
        nodes, _, _ = w.get_latex_nodes()
        doc_nodes = [n for n in nodes if isinstance(n, LatexEnvironmentNode)]
        if len(doc_nodes) > 1:
            raise ValueError("Multiple documents in a single file are not supported.")
        children: List[TexNode] = [v for n in doc_nodes[0].nodelist for v in convert(n)]
        doc = TexDocNode(
            name='document',
            children=children,
            group_latex_expr=''.join(n.latex_verbatim() for n in doc_nodes[0].nodelist),
            prefix='',
            suffix='')
        # Extract equations from the document.
        self._extract_equations(doc)
        return doc
    
    def parse(self, tex: str) -> TexDocNode:
        """
        Get a LaTeX document from a TeX string.
        
        :param tex: The TeX string.

        :return: The LaTeX document.
        """
        w = LatexWalker(tex)
        nodes, _, _ = w.get_latex_nodes()
        children: List[TexNode] = [v for n in nodes for v in convert(n)]
        doc = TexDocNode(
            name='document',
            children=children,
            group_latex_expr=''.join(n.latex_verbatim() for n in nodes),
            prefix='',
            suffix='')
        # Extract equations from the document.
        self._extract_equations(doc)
        return doc

    def get_converter(self, node: TexNode) -> Converter:
        """ Get the converter for a LaTeX node. """
        return self.__converters.get(
            node.get_node_type(), 
            self.__default_converters.get(type(node), None))
    
    def set_converter(self, node_type: Type[TexNode], name: str, converter: Converter) -> None:
        """
        Set a converter for a LaTeX node type. For `TexMacroNode` and `TexEnvNode` the name of the node must be
        the same as the name of the LaTeX macro or environment, for example `\\section` have name `section`; and
        `\\begin{equation}...\\end{equation}` have name `equation`. For `TexGroupNode` the name can be a string
        indicating its decorator names in ascending order delimited by `:`, for example `{\\topic{...} ... \\label{...} ...}`
        have name `label:topic`.
        
        :param node_type: The type of the LaTeX node.
        :param name: The name of the LaTeX node.
        :param converter: The converter for the LaTeX node.
        """
        self.__converters[(node_type, name)] = converter

    def set_default_converter(self, node_type: Type[TexNode], converter: Converter) -> None:
        """
        Set a default converter for a LaTeX node type. This converter will be used when a specific converter is not
        found for a LaTeX node.
        
        :param node_type: The type of the LaTeX node.
        :param converter: The converter for the LaTeX node.
        """
        self.__default_converters[node_type] = converter
    
    def to_md(self, doc: TexDocNode) -> MdDocument:
        """
        Convert a LaTeX document to a markdown document.
        
        :param doc: The LaTeX document to be converted.
        
        :return: The markdown document.
        """
        doc.remove(type=TexMacroNode, name='label', deep=True)
        pipeline = ((self.get_converter(node), node) for node in doc.children)
        children = [v for converter, node in pipeline if converter is not None 
                    for v in converter.convert(node)]
        return MdDocument(children=children)
    
    def get_ref_type(self, label: str) -> str:
        """
        Get the type of a LaTeX ref label.

        :param label: The label of the reference.

        :return: The type of the reference, returns an empty string if the label is not found.
        """
        return self.__refs.get(label, (-1, '', None))[1]
        
    def _extract_equations(self, doc: TexDocNode) -> None:
        """ Extract equations from a LaTeX document and store them with the sequential ids. """
        gen = ((self._parse_ref_name(eqn), eqn) for eqn in doc.find(TexEnvNode, 'equation', deep=True))
        gen = ((label, eqn) for label, eqn in gen if label)
        self.__refs |= {label: (n, 'equation', eqn) for n, (label, eqn) in enumerate(gen)}
        self.__ref_names |= {id(eqn): label for label, (_, _, eqn) in self.__refs.items()}

    def _get_ref_id(self, label: str) -> int:
        """
        Get the sequential id of a LaTeX ref label.
        
        :param label: The label of the reference.
        
        :return: The id of the reference, returns `-1` if the label is not found.
        """
        return self.__refs.get(label, (-1, '', None))[0]

    def _parse_ref_name(self, node: TexEnvNode) -> str:
        """ Parse the name of the environment node from the label children node. """
        labels = node.find(TexMacroNode, 'label', deep=True)
        if not labels: return ''
        return labels[0].children[0].children[0].text
    
    def _get_ref_name(self, node: TexEnvNode) -> str:
        """ Get the label of a LaTeX ref node. """
        return self.__ref_names.get(id(node), '')
