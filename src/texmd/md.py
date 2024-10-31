from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from typing import List
import re


class MdNode(BaseModel, ABC):
    """ Abstract class for markdown nodes. """

    @abstractmethod
    def to_str(self) -> str:
        """ Convert the node to a markdown string. """
        pass

class MdBranchNode(MdNode, ABC):
    """ Abstract class for markdown nodes that have children. """

    children: List[MdNode] = Field(description="The children of the node.")

    def content_to_str(self) -> str:
        return "".join(child.to_str() for child in self.children)
    

MD_UNSUPPORTED_MACRO = [
    # \label{...}
    r'\\label\{[^\}]*\}']


class MdDocument(MdBranchNode):
    """ A markdown document node. """

    def to_str(self) -> str:
        # Regex to match the specific LaTeX macro \label{<Some Text>}
        content = self.content_to_str()
        for pattern in MD_UNSUPPORTED_MACRO:
            regex = re.compile(pattern)
            content = regex.sub("", content)
        return content
    

class MdHeading(MdBranchNode):
    """ A markdown heading node. """

    def to_str(self) -> str:
        return f"# {self.content_to_str()}\n"
    

class MdSubHeading(MdBranchNode):
    """ A markdown sub-heading node. """

    def to_str(self) -> str:
        return f"## {self.content_to_str()}\n"
    

class MdSubSubHeading(MdBranchNode):
    """ A markdown sub-sub-heading node. """

    def to_str(self) -> str:
        return f"### {self.content_to_str()}\n"
    

class MdSubSubSubHeading(MdBranchNode):
    """ A markdown sub-sub-sub-heading node. """

    def to_str(self) -> str:
        return f"#### {self.content_to_str()}\n"


class MdText(MdNode):
    """ A markdown text node. """

    text: str = Field(description="The text of the node.")

    def to_str(self) -> str:
        return self.text
    

class MdBold(MdText):
    """ A markdown bold text node. """

    def to_str(self) -> str:
        return f"**{self.text}**"
    

class MdItalic(MdText):
    """ A markdown italic text node. """

    def to_str(self) -> str:
        return f"*{self.text}*"
    

class MdBlockQuote(MdBranchNode):
    """ A markdown block quote node. """

    def to_str(self) -> str:
        lines = self.content_to_str().split("\n")
        return "\n".join(["> " + line for line in lines])
        
    
class MdUnorderedList(MdText):
    """ A markdown unordered list node. """

    def to_str(self) -> str:
        return f"- {self.text}\n"
    

class MdOrderedList(MdText):
    """ A markdown ordered list node. """

    number: int = Field(description="The number of the list item.")

    def to_str(self) -> str:
        return f"{self.number}. {self.text}\n"


class MdMath(MdNode):
    """ A markdown math node. """

    tex: str = Field(description="The LaTeX code of the math node.")

    def to_str(self) -> str:
        return f"${self.tex}$"


MD_EQ = """
```math
{tex}
```
"""


class MdEquation(MdNode):
    """ A markdown equation node. """

    tex: str = Field(description="The LaTeX code of the equation node.")

    def to_str(self) -> str:
        return MD_EQ.format(tex=self.tex)
