"""A module for locatable records."""


class Locatable(object):
    """A class that defines a genomic location (or span)."""

    def __init__(self, chromosome, start, end):
        self._chromosome = chromosome
        self._start = start
        self._end = end

    @property
    def chromosome(self):
        """Returns the chromosome name"""
        return self._chromosome

    @chromosome.setter
    def chromosome(self, value):
        """Sets the chromosome position"""
        self._chromosome = value

    @property
    def start(self):
        """Returns the start position"""
        return self._start

    @start.setter
    def start(self, value):
        """Sets the start position"""
        self._start = value

    @property
    def end(self):
        """Returns the end position"""
        return self._end

    @end.setter
    def end(self, value):
        """Sets the end position"""
        self._end = value


class LocatableByAllele(Locatable):
    """A class that defines a genomic location (or span), with an associated
    reference and set of alternate alleles (may be empty)"""

    def __init__(self, chromosome, start, end, ref, alts):
        self._ref = ref
        self._alts = alts
        super(LocatableByAllele, self).__init__(chromosome, start, end)

    @property
    def ref(self):
        """Returns the reference allele"""
        return self._ref

    @property
    def alts(self):
        """Returns a list of valid alternate alleles"""
        return self._alts
