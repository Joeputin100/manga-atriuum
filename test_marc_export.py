#!/usr/bin/env python3
"""
Test MARC Export for Atriuum Import

Creates multiple test MARC records with bibliographic and holding information
for testing import into Atriuum library system.
"""

import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from manga_lookup import BookInfo
from marc_exporter import export_books_to_marc


def create_test_books():
    """Create test book data for MARC export"""

    test_books = [
        # Book 1: Tokyo Ghoul Volume 1
        BookInfo(
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
            warnings=["MSRP $12.99 is within expected range"]
        ),

        # Book 2: One Piece Volume 1 (with MSRP under $10)
        BookInfo(
            series_name="One Piece",
            volume_number=1,
            book_title="One Piece (Volume 1)",
            authors=["Oda, Eiichiro"],
            msrp_cost=9.99,
            isbn_13="9781569319017",
            publisher_name="VIZ Media LLC",
            copyright_year=2003,
            description="Monkey D. Luffy begins his journey to become the Pirate King by gathering a crew and searching for the legendary treasure One Piece.",
            physical_description="208 pages : chiefly illustrations ; 19 cm",
            genres=["Shonen", "Adventure", "Fantasy", "Comedy"],
            warnings=["MSRP $9.99 is below minimum $10 (rounded up to $10.0)"]
        ),

        # Book 3: Naruto Volume 1
        BookInfo(
            series_name="Naruto",
            volume_number=1,
            book_title="Naruto (Volume 1)",
            authors=["Kishimoto, Masashi"],
            msrp_cost=9.99,
            isbn_13="9781569319000",
            publisher_name="VIZ Media LLC",
            copyright_year=2003,
            description="Naruto Uzumaki, a young ninja who seeks recognition from his peers and dreams of becoming the Hokage, the leader of his village.",
            physical_description="192 pages : chiefly illustrations ; 19 cm",
            genres=["Shonen", "Action", "Adventure", "Martial Arts"],
            warnings=["MSRP $9.99 is below minimum $10 (rounded up to $10.0)"]
        ),

        # Book 4: Attack on Titan Volume 1
        BookInfo(
            series_name="Attack on Titan",
            volume_number=1,
            book_title="Attack on Titan (Volume 1)",
            authors=["Isayama, Hajime"],
            msrp_cost=10.99,
            isbn_13="9781612620244",
            publisher_name="Kodansha Comics",
            copyright_year=2012,
            description="In a world where the last of humanity lives within three concentric walls, protecting them from gigantic, man-eating Titans, Eren Yeager vows to cleanse the earth of the Titan menace.",
            physical_description="192 pages : chiefly illustrations ; 20 cm",
            genres=["Action", "Dark Fantasy", "Post-apocalyptic", "Horror"],
            warnings=[]
        ),

        # Book 5: My Hero Academia Volume 1
        BookInfo(
            series_name="My Hero Academia",
            volume_number=1,
            book_title="My Hero Academia (Volume 1)",
            authors=["Horikoshi, Kohei"],
            msrp_cost=9.99,
            isbn_13="9781421582696",
            publisher_name="VIZ Media LLC",
            copyright_year=2015,
            description="In a world where most people have superpowers, middle school student Izuku Midoriya wants to be a hero more than anything, but he hasn't got an ounce of power in him.",
            physical_description="192 pages : chiefly illustrations ; 19 cm",
            genres=["Shonen", "Superhero", "Action", "School Life"],
            warnings=["MSRP $9.99 is below minimum $10 (rounded up to $10.0)"]
        ),

        # Book 6: Demon Slayer Volume 1
        BookInfo(
            series_name="Demon Slayer",
            volume_number=1,
            book_title="Demon Slayer: Kimetsu no Yaiba (Volume 1)",
            authors=["Gotouge, Koyoharu"],
            msrp_cost=9.99,
            isbn_13="9781974700523",
            publisher_name="VIZ Media LLC",
            copyright_year=2018,
            description="In Taisho-era Japan, kindhearted Tanjiro Kamado makes a living selling charcoal. But his peaceful life is shattered when a demon slaughters his entire family.",
            physical_description="192 pages : chiefly illustrations ; 19 cm",
            genres=["Shonen", "Supernatural", "Action", "Historical"],
            warnings=["MSRP $9.99 is below minimum $10 (rounded up to $10.0)"]
        ),

        # Book 7: Jujutsu Kaisen Volume 1
        BookInfo(
            series_name="Jujutsu Kaisen",
            volume_number=1,
            book_title="Jujutsu Kaisen (Volume 1)",
            authors=["Akutami, Gege"],
            msrp_cost=9.99,
            isbn_13="9781974710027",
            publisher_name="VIZ Media LLC",
            copyright_year=2019,
            description="Yuji Itadori is high schooler who spends his days visiting his bedridden grandfather. Although he looks like your average teenager, his immense physical strength is something to behold!",
            physical_description="192 pages : chiefly illustrations ; 19 cm",
            genres=["Shonen", "Supernatural", "Action", "Horror"],
            warnings=["MSRP $9.99 is below minimum $10 (rounded up to $10.0)"]
        ),

        # Book 8: Chainsaw Man Volume 1
        BookInfo(
            series_name="Chainsaw Man",
            volume_number=1,
            book_title="Chainsaw Man (Volume 1)",
            authors=["Fujimoto, Tatsuki"],
            msrp_cost=9.99,
            isbn_13="9781974709939",
            publisher_name="VIZ Media LLC",
            copyright_year=2020,
            description="Denji is a young man who will do anything for money, even hunting down devils with his pet devil Pochita. He's a simple man with simple dreams, drowning under a mountain of debt.",
            physical_description="192 pages : chiefly illustrations ; 19 cm",
            genres=["Shonen", "Action", "Supernatural", "Dark Comedy"],
            warnings=["MSRP $9.99 is below minimum $10 (rounded up to $10.0)"]
        ),

        # Book 9: Spy x Family Volume 1
        BookInfo(
            series_name="Spy x Family",
            volume_number=1,
            book_title="Spy x Family (Volume 1)",
            authors=["Endo, Tatsuya"],
            msrp_cost=9.99,
            isbn_13="9781974720521",
            publisher_name="VIZ Media LLC",
            copyright_year=2019,
            description="Master spy Twilight must build a fake family and execute a perfect mission to maintain world peace. What he doesn't know is that the wife he's chosen is an assassin and the child he's adopted is a telepath!",
            physical_description="192 pages : chiefly illustrations ; 19 cm",
            genres=["Shonen", "Action", "Comedy", "Slice of Life"],
            warnings=["MSRP $9.99 is below minimum $10 (rounded up to $10.0)"]
        ),

        # Book 10: Boruto: Naruto Next Generations Volume 1
        BookInfo(
            series_name="Boruto: Naruto Next Generations",
            volume_number=1,
            book_title="Boruto: Naruto Next Generations (Volume 1)",
            authors=["Kodachi, Ukyo", "Kishimoto, Masashi"],
            msrp_cost=9.99,
            isbn_13="9781421592114",
            publisher_name="VIZ Media LLC",
            copyright_year=2017,
            description="Naruto was a young shinobi with an incorrigible knack for mischief. He achieved his dream to become the greatest ninja in his village, and now his face sits atop the Hokage monument.",
            physical_description="192 pages : chiefly illustrations ; 19 cm",
            genres=["Shonen", "Action", "Adventure", "Martial Arts"],
            warnings=["MSRP $9.99 is below minimum $10 (rounded up to $10.0)"]
        )
    ]

    return test_books


def main():
    """Generate test MARC file for Atriuum import"""
    print("Generating test MARC records for Atriuum import...")

    # Create test books
    test_books = create_test_books()

    print(f"Created {len(test_books)} test manga records")

    # Export to MARC file
    output_file = "test_manga_collection.mrc"
    export_books_to_marc(test_books, output_file, "T")

    print(f"\nTest MARC file generated: {output_file}")
    print("\nRecord Summary:")
    print("=" * 60)

    for i, book in enumerate(test_books, 1):
        holding_barcode = f"T{i:06d}"
        print(f"{i:2d}. {book.series_name} Vol.{book.volume_number}")
        print(f"     Title: {book.book_title}")
        print(f"     Author: {', '.join(book.authors)}")
        print(f"     ISBN: {book.isbn_13}")
        print(f"     Barcode: {holding_barcode}")
        print(f"     MSRP: ${book.msrp_cost:.2f}")
        if book.warnings:
            print(f"     Warnings: {', '.join(book.warnings)}")
        print()

    print("=" * 60)
    print("\n✓ Test MARC export completed successfully!")
    print("\nInstructions for Atriuum import:")
    print("1. Open Atriuum and navigate to Cataloging")
    print("2. Select 'Import MARC Records'")
    print("3. Choose the file: test_manga_collection.mrc")
    print("4. Map fields according to your library's configuration")
    print("5. Pay special attention to the 852 field for holding information")
    print("6. Test with a small batch first before importing all records")


if __name__ == "__main__":
    main()