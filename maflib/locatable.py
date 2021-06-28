"""A module for locatable records."""


from typing import List, Optional, Union


class Locatable:
    """A class that defines a genomic location (or span)."""

    def __init__(
        self,
        chromosome: Optional[Union[str, int]],
        start: Optional[int],
        end: Optional[int],
    ):
        self._chromosome = chromosome
        self._start = start
        self._end = end

    @property
    def chromosome(self) -> Optional[Union[str, int]]:
        """Returns the chromosome name"""
        return self._chromosome

    @chromosome.setter
    def chromosome(self, value: Union[str, int]) -> None:
        """Sets the chromosome position"""
        self._chromosome = value

    @property
    def start(self) -> Optional[int]:
        """Returns the start position"""
        return self._start

    @start.setter
    def start(self, value: int) -> None:
        """Sets the start position"""
        self._start = value

    @property
    def end(self) -> Optional[int]:
        """Returns the end position"""
        return self._end

    @end.setter
    def end(self, value: int) -> None:
        """Sets the end position"""
        self._end = value


class LocatableByAllele(Locatable):
    """Defines a genomic location (or span) with ref and alt alleles."""

    def __init__(
        self,
        chromosome: Optional[Union[int, str]],
        start: Optional[int],
        end: Optional[int],
        ref: Optional[str],
        alts: Optional[List[str]],
    ):
        self._ref = ref
        self._alts = alts
        super(LocatableByAllele, self).__init__(chromosome, start, end)

    @property
    def ref(self) -> Optional[str]:
        """Returns the reference allele"""
        return self._ref

    @property
    def alts(self) -> Optional[List[str]]:
        """Returns a list of valid alternate alleles"""
        return self._alts
