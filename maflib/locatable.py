"""A module for locatable records."""


from typing import List, Union


class Locatable:
    """A class that defines a genomic location (or span)."""

    def __init__(self, chromosome: Union[str, int], start: int, end: int):
        self._chromosome = chromosome
        self._start = start
        self._end = end

    @property
    def chromosome(self) -> Union[str, int]:
        """Returns the chromosome name"""
        return self._chromosome

    @chromosome.setter
    def chromosome(self, value: Union[str, int]) -> None:
        """Sets the chromosome position"""
        self._chromosome = value

    @property
    def start(self) -> int:
        """Returns the start position"""
        return self._start

    @start.setter
    def start(self, value: int) -> None:
        """Sets the start position"""
        self._start = value

    @property
    def end(self) -> int:
        """Returns the end position"""
        return self._end

    @end.setter
    def end(self, value: int) -> None:
        """Sets the end position"""
        self._end = value


class LocatableByAllele(Locatable):
    """Defines a genomic location (or span) with ref and alt alleles.
    """

    def __init__(
        self, chromosome: str, start: int, end: int, ref: str, alts: List[str]
    ):
        self._ref = ref
        self._alts = alts
        super(LocatableByAllele, self).__init__(chromosome, start, end)

    @property
    def ref(self) -> str:
        """Returns the reference allele"""
        return self._ref

    @property
    def alts(self) -> List[str]:
        """Returns a list of valid alternate alleles"""
        return self._alts
