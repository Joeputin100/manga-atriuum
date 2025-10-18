#!/usr/bin/env python3
"""
MARC Exporter for Manga Lookup Tool

Creates MARC21 bibliographic and holding records compatible with Atriuum
"""

import os
import sys
from datetime import datetime

from pymarc import Field, Record, Subfield

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from manga_lookup import BookInfo, DataValidator


def generate_call_number(book: BookInfo, holding_barcode: str) -> str:
    """
    Generate call number in format: "FIC {first 3 letters of author's last name} {copyright year} {holding barcode}"

    Args:
        book: BookInfo object
        holding_barcode: Barcode for the holding

    Returns:
        Formatted call number string
    """
    # Get first author
    if not book.authors:
        return f"FIC UNK {book.copyright_year or '0000'} {holding_barcode}"

    first_author = book.authors[0]

    # Extract last name (first part before comma)
    if ", " in first_author:
        last_name = first_author.split(", ")[0]
    else:
        # If no comma, assume the last word is the last name
        name_parts = first_author.split()
        last_name = name_parts[-1] if name_parts else "UNK"

    # Get first 3 letters of last name, uppercase
    author_code = last_name[:3].upper() if len(last_name) >= 3 else last_name.upper()

    # Get copyright year or use 0000 if none
    year = book.copyright_year or 0000

    return f"FIC {author_code} {year} {holding_barcode}"


def create_marc_record(book: BookInfo, holding_barcode: str = "T000001") -> Record:
    """
    Create a MARC21 bibliographic record from BookInfo

    Args:
        book: BookInfo object containing manga data
        holding_barcode: Barcode for the holding record

    Returns:
        pymarc.Record object
    """
    record = Record()

    # Generate control number from ISBN or create one
    control_number = book.isbn_13.replace("-", "") if book.isbn_13 else f"M{book.volume_number:03d}"

    # Control Fields
    record.add_field(Field(tag="001", data=control_number))
    record.add_field(Field(tag="003", data="OCoLC"))
    record.add_field(Field(tag="005", data=datetime.now().strftime("%Y%m%d%H%M%S.0")))

    # Fixed-Length Data Elements (008 field)
    # Format: Date1 Type Date2 Country Illus Audn Form Cont GPub LitF Biog Lang
    current_year = datetime.now().year
    pub_year = book.copyright_year if book.copyright_year else current_year

    # Create 008 field data
    # Positions: 00-05: Date entered, 06: Type, 07-10: Date1, 11-14: Date2, 15-17: Country,
    # 18-21: Illus, 22: Target audience, 23: Form, 24-27: Nature of contents, 28: Govt pub,
    # 29: Conference, 30: Festschrift, 31: Index, 32: Main entry, 33-34: Fiction, 35-37: Biography
    # 38: Language, 39: Modified record

    date_entered = datetime.now().strftime("%y%m%d")
    type_code = "a"  # Language material
    date1 = str(pub_year)
    date2 = "\\"  # No date2
    country = "xxu"  # Unknown country
    illus = "    "  # No illustrations specified
    audn = " "  # Unknown target audience
    form = " "  # Not specified
    cont = "    "  # No nature of contents
    gpub = " "  # Not government publication
    lang = "eng"  # English

    # Build 008 field
    field_008 = f"{date_entered}{type_code}{date1}{date2}{country}{illus}{audn}{form}{cont}{gpub} 0 {lang} d"
    record.add_field(Field(tag="008", data=field_008))

    # 020 - ISBN
    if book.isbn_13:
        subfields = [Subfield("a", book.isbn_13)]
        if book.msrp_cost:
            subfields.append(Subfield("c", f"${book.msrp_cost:.2f}"))
        record.add_field(Field(
            tag="020",
            indicators=[" ", " "],
            subfields=subfields,
        ))

    # 040 - Cataloging Source
    record.add_field(Field(
        tag="040",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "OCoLC"),
            Subfield("b", "eng"),
            Subfield("c", "OCoLC"),
            Subfield("e", "rda"),
        ],
    ))

    # 100 - Main Entry - Personal Name (Author)
    if book.authors:
        formatted_authors = DataValidator.format_authors_list(book.authors)
        record.add_field(Field(
            tag="100",
            indicators=["1", " "],
            subfields=[Subfield("a", formatted_authors)],
        ))

    # 245 - Title Statement
    # Indicator 1: 1 = Added entry, Indicator 0: 0 = No nonfiling characters
    title_field = Field(
        tag="245",
        indicators=["1", "0"],
        subfields=[Subfield("a", book.book_title)],
    )

    # Add responsibility statement if authors exist
    if book.authors:
        formatted_authors = DataValidator.format_authors_list(book.authors)
        title_field.subfields.append(Subfield("c", formatted_authors))

    record.add_field(title_field)

    # 264 - Production, Publication, Distribution, Manufacture
    if book.publisher_name or book.copyright_year:
        subfields = []
        if book.publisher_name:
            subfields.append(Subfield("b", book.publisher_name))
        if book.copyright_year:
            subfields.append(Subfield("c", str(book.copyright_year)))

        record.add_field(Field(
            tag="264",
            indicators=[" ", "1"],  # First publisher, production
            subfields=subfields,
        ))

    # 300 - Physical Description
    if book.physical_description:
        record.add_field(Field(
            tag="300",
            indicators=[" ", " "],
            subfields=[Subfield("a", book.physical_description)],
        ))
    else:
        # Default physical description for manga
        record.add_field(Field(
            tag="300",
            indicators=[" ", " "],
            subfields=[Subfield("a", "1 volume (unpaged) : chiefly illustrations ; 19 cm")],
        ))

    # 336-338 - RDA Content, Media, and Carrier Types
    # Content type: still image (manga)
    record.add_field(Field(
        tag="336",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "still image"),
            Subfield("b", "sti"),
            Subfield("2", "rdacontent"),
        ],
    ))

    # Media type: unmediated
    record.add_field(Field(
        tag="337",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "unmediated"),
            Subfield("b", "n"),
            Subfield("2", "rdamedia"),
        ],
    ))

    # Carrier type: volume
    record.add_field(Field(
        tag="338",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "volume"),
            Subfield("b", "nc"),
            Subfield("2", "rdacarrier"),
        ],
    ))

    # 490 - Series Statement
    if book.series_name:
        record.add_field(Field(
            tag="490",
            indicators=["1", " "],  # Series traced differently
            subfields=[
                Subfield("a", book.series_name),
                Subfield("v", str(book.volume_number)),
            ],
        ))

    # 520 - Summary
    if book.description:
        record.add_field(Field(
            tag="520",
            indicators=[" ", " "],
            subfields=[Subfield("a", book.description[:500])],  # Limit length
        ))

    # 500 - General Notes
    # Format: "Manga, genre1, genre2, genre3"
    if book.genres:
        notes_text = f"Manga, {', '.join(book.genres)}"
        record.add_field(Field(
            tag="500",
            indicators=[" ", " "],
            subfields=[Subfield("a", notes_text)],
        ))

    # 650 - Subject Headings
    # Add genres as subject headings
    if book.genres:
        for genre in book.genres:
            record.add_field(Field(
                tag="650",
                indicators=[" ", "0"],  # LCSH
                subfields=[
                    Subfield("a", genre),
                    Subfield("v", "Comic books, strips, etc."),
                ],
            ))

    # Add manga as a subject
    record.add_field(Field(
        tag="650",
        indicators=[" ", "0"],
        subfields=[
            Subfield("a", "Manga"),
            Subfield("v", "Comic books, strips, etc."),
        ],
    ))

    # 852 - Location (Holding Information)
    # Using indicator 8 for "Other scheme"
    record.add_field(Field(
        tag="852",
        indicators=["8", " "],
        subfields=[
            Subfield("b", "Main Library"),  # Shelving location: Main Library
            Subfield("h", generate_call_number(book, holding_barcode)),  # Local call number
            Subfield("p", holding_barcode),  # Barcode
            Subfield("x", "Manga collection"),  # Public note
        ],
    ))

    # 090 - Local Call Number (LOC)
    # Format: "FIC {first 3 letters of author's last name} {copyright year} {holding barcode}"
    if book.authors:
        call_number = generate_call_number(book, holding_barcode)
        record.add_field(Field(
            tag="090",
            indicators=[" ", " "],
            subfields=[Subfield("a", call_number)],
        ))

    return record


def export_books_to_marc(books: list[BookInfo], output_file: str, holding_barcode_prefix: str = "T"):
    """
    Export a list of books to MARC file

    Args:
        books: List of BookInfo objects
        output_file: Path to output MARC file
        holding_barcode_prefix: Prefix for holding barcodes (used as fallback)
    """
    records = []

    for i, book in enumerate(books, 1):
        # Use the book's assigned barcode if available, otherwise generate one
        if book.barcode:
            holding_barcode = book.barcode
        else:
            holding_barcode = f"{holding_barcode_prefix}{i:06d}"
        record = create_marc_record(book, holding_barcode)
        records.append(record)

    # Write records to file
    with open(output_file, "wb") as out:
        for record in records:
            out.write(record.as_marc())

    print(f"Exported {len(records)} MARC records to {output_file}")


def create_test_marc_record():
    """
    Create a test MARC record with dummy data for Atriuum import testing
    """
    from manga_lookup import BookInfo

    # Create test book data
    test_book = BookInfo(
        series_name="Tokyo Ghoul",
        volume_number=1,
        book_title="Tokyo Ghoul (Volume 1)",
        authors=["Ishida, Sui"],
        msrp_cost=12.99,
        isbn_13="9781421580366",
        publisher_name="VIZ Media LLC",
        copyright_year=2015,
        description="In modern-day Tokyo, shy college student Ken Kaneki's life changes forever when he becomes a half-ghoul after a fateful encounter. He must navigate the dangerous world of ghouls while trying to maintain his humanity.",
        physical_description="224 pages : chiefly illustrations ; 19 cm",
        genres=["Horror", "Dark Fantasy", "Seinen", "Supernatural"],
        warnings=["MSRP $12.99 is within expected range"],
    )

    return create_marc_record(test_book, "T000001")


if __name__ == "__main__":
    # Test the MARC exporter
    print("Testing MARC exporter...")

    test_record = create_test_marc_record()

    # Display the record
    print("\nTest MARC Record:")
    print("=" * 60)
    for field in test_record.fields:
        print(f"{field.tag}: {field}")

    # Save test record
    with open("test_manga_record.mrc", "wb") as out:
        out.write(test_record.as_marc())

    print("\nTest record saved to test_manga_record.mrc")
    print("✓ MARC exporter test completed successfully!")
