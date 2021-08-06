"""
Stores the values for columns with custom types, typically stored in
Enumerations.
"""
from enum import Enum, unique


class MafEnum(Enum):
    """An enumeration that whose string representation is its value as a
    string"""

    def __str__(self) -> str:
        return str(self.value)


@unique
class NullableYesOrNoEnum(MafEnum):
    """Enumeration for "Yes" or "No" column values, with Null being
    non-value"""

    Null: str = ""
    No: str = "0"
    Yes: str = "1"


@unique
class NullableYOrNEnum(MafEnum):
    """Enumeration for "Y" or "N" column values, with Null being non-value"""

    Null = ""
    No = "N"
    Yes = "Y"


@unique
class YesNoOrUnknownEnum(MafEnum):
    """Enumeration for "Yes", "No", "Unknown" column values."""

    Unknown = "Unknown"
    No = "No"
    Yes = "Yes"


@unique
class PickEnum(MafEnum):
    """Enumeration for the MAF 'Pick' column value"""

    Null: str = ""
    Yes: str = "1"


@unique
class StrandEnum(MafEnum):
    """Enumeration for the MAF 'Strand' column value"""

    Plus: str = '+'
    Minus: str = '-'


@unique
class VariantClassificationEnum(MafEnum):
    """Enumeration for the MAF 'Variant_Classification' column value"""

    FrameShiftDeletion: str = "Frame_Shift_Del"
    FrameShiftInsertion: str = "Frame_Shift_Ins"
    InFrameInsertion: str = "In_Frame_Ins"
    InFrameDeletion: str = "In_Frame_Del"
    MissenseMutation: str = "Missense_Mutation"
    Nonsense_Mutation: str = "Nonsense_Mutation"
    Silent: str = "Silent"
    SpliceSite: str = "Splice_Site"
    Translation_Start_Site: str = "Translation_Start_Site"
    Nonstop_Mutation: str = "Nonstop_Mutation"
    ThreePrimerUtr: str = "3'UTR"
    ThreePrimeFlank: str = "3'Flank"
    FivePrimerUtr: str = "5'UTR"
    FivePrimeFlank: str = "5'Flank"
    IGR: str = "IGR"
    Intron: str = "Intron"
    RNA: str = "RNA"
    TargetedRegion: str = "Targeted_Region"
    SpliceRegion: str = "Splice_Region"


@unique
class VariantTypeEnum(MafEnum):
    """Enumeration for the MAF 'Variant_Type' column value"""

    SNP: str = "SNP"
    DNP: str = "DNP"
    TNP: str = "TNP"
    ONP: str = "ONP"
    INS: str = "INS"
    DEL: str = "DEL"
    Consolidated: str = "Consolidated"


@unique
class VerificationStatusEnum(MafEnum):
    """Enumeration for the MAF 'Verification_Status' column value"""

    Verified: str = "Verified"
    Unknown: str = "Unknown"


@unique
class MutationStatusEnum(MafEnum):
    """Enumeration for the MAF 'Mutation_Status' column value"""

    NoStatus: str = "None"
    Germline: str = "Germline"
    Somatic: str = "Somatic"
    LOH: str = "LOH"
    PostTranscriptional: str = "Post - transcriptional"
    Modification: str = "modification"
    Unknown: str = "Unknown"


@unique
class ValidationStatusEnum(MafEnum):
    """Enumeration for the MAF 'Validation_Status' column value"""

    Untested: str = "Untested"
    Inconclusive: str = "Inconclusive"
    Valid: str = "Valid"
    Invalid: str = "Invalid"


@unique
class SequencerEnum(MafEnum):
    """Enumeration for the MAF 'Sequencer' column value"""

    ABIThirtySevenThirty: str = "ABI 3730xl"
    ABSOLiDFourSystem: str = "AB SOLiD 4 System"
    ABSOLiDTwoSystem: str = "AB SOLiD 2 System"
    ABSOLiDThreeSystem: str = "AB SOLiD 3 System"
    CompleteGenomics: str = "Complete Genomics"
    FourFiveFour: str = "454"
    FourFiveFourFLXTitanium: str = "454 GS FLX Titanium"
    IlluminaGaII: str = "Illumina Genome Analyzer II"
    IlluminaGaIIx: str = "Illumina GAIIx"
    IlluminaGaIIxLong: str = "Illumina Genome Analyzer IIx"
    IlluminaHiSeq: str = "Illumina HiSeq"
    IlluminaHiSeqTwoThousand: str = "Illumina HiSeq 2000"
    IlluminaHiSeqTwentyFiveHundred: str = "Illumina HiSeq 2500"
    IlluminaHiSeqFourThousand: str = "Illumina HiSeq 4000"
    IlluminaHiSeqXTen: str = "Illumina HiSeq X Ten"
    IlluminaHiSeqXFive: str = "Illumina HiSeq X Five"
    IlluminaMiSeq: str = "Illumina MiSeq"
    IlluminaNextSeq: str = "Illumina NextSeq"
    IonTorrentPGM: str = "Ion Torrent PGM"
    IonTorrentProton: str = "Ion Torrent Proton"
    PacBioRS: str = "PacBio RS"
    SOLID: str = "SOLID"
    Other: str = "Other"


@unique
class FeatureTypeEnum(MafEnum):
    """Enumeration for the MAF 'Feature_Type' column value"""

    Transcript: str = "Transcript"
    RegulatoryFeature: str = "RegulatoryFeature"
    MotifFeature: str = "MotifFeature"


@unique
class ImpactEnum(MafEnum):
    """Enumeration for the MAF 'Impact' column value"""

    Modifier: str = "MODIFIER"
    Low: str = "LOW"
    Moderate: str = "MODERATE"
    High: str = "HIGH"


@unique
class MC3OverlapEnum(MafEnum):
    """Enumeration for the MAF 'MC3_Overlap' column value"""

    Unknown: str = "Unknown"
    _True: str = "True"
    _False: str = "False"


@unique
class GdcValidationStatusEnum(MafEnum):
    """Enumeration for the MAF 'GDC_Validation_Status' column value"""

    Unknown: str = "Unknown"
    Valid: str = "Valid"
    Invalid: str = "Invalid"
    Inconclusive: str = "Inconclusive"
