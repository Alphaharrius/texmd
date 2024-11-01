from pybtex.database.input import bibtex, BibliographyData
from pybtex.database import Entry, Person
from pylatexenc.latexwalker import LatexMacroNode, LatexGroupNode, LatexCharsNode
from pylatexenc.macrospec import ParsedMacroArgs

from typing import LiteralString, List

from texmd.texmd import Converter
from texmd.md import MdNode, MdText


def build_cite_converter(bib_file: LiteralString) -> 'CiteConverter':
    """
    Build a converter for LaTeX Cite nodes.
    
    :param bib_file: The path to the BibTeX file.
    """
    parser = bibtex.Parser()
    bib = parser.parse_file(bib_file)
    return CiteConverter(bib)


class CiteConverter(Converter):
    """ A converter for LaTeX Cite nodes. """

    def __init__(self, bib_data: BibliographyData):
        self.bib_data = bib_data

    def convert(self, node: LatexMacroNode) -> MdNode:
        arguments: ParsedMacroArgs = node.nodeargd
        arg_nodes = [n for n in arguments.argnlist if n is not None]
        group_node: LatexGroupNode = arg_nodes[0]
        chars_node: LatexCharsNode = group_node.nodelist[0]
        cite_names = chars_node.chars.replace(' ', '').split(',')

        def get_citation(entry: Entry):
            citation = []

            authors: List[Person] = entry.persons['author']
            for author in authors:
                first_name = " ".join(author.first_names)
                middle_name = " ".join(author.middle_names)
                last_name = " ".join(author.last_names)
                first_abbrev = (first_name[0] + '.' if first_name else '')
                middle_abbrev = (middle_name[0] + '.' if middle_name else '')
                name = f"{first_abbrev} {middle_abbrev} {last_name}"
                citation.append(name)
                citation.append(', ')

            title = entry.fields['title']
            citation.append(title)
            citation.append(', ')

            year = entry.fields['year'] if 'year' in entry.fields else '<UNKNOWN DATE>'
            citation.append(year)

            return "`" + "".join(citation) + "`"

        citations = (
            get_citation(self.bib_data.entries[cite_name]) if cite_name in self.bib_data.entries else '<UNKNOWN>' 
            for cite_name in cite_names)
        
        return MdText(text="(" + ", ".join(citations) + ")")
