from pydantic import BaseModel
from typing import List


class Author(BaseModel):
    """ An author of a bibliography entry. """

    first_name: str
    """ The first name of the author. """

    middle_name: str
    """ The middle name of the author. """

    last_name: str
    """ The last name of the author. """


class Entry(BaseModel):
    """ A bibliography entry. """

    name: str
    """ The name of the entry. """

    authors: List[Author]
    """ The authors of the entry. """

    title: str
    """ The title of the entry. """

    year: str
    """ The year of the entry. """

    journal: str
    """ The journal of the entry. """

    volume: str
    """ The volume of the entry. """

    number: str
    """ The number of the entry. """

    pages: str
    """ The pages of the entry. """

    doi: str
    """ The DOI of the entry. """

    url: str
    """ The URL of the entry. """
