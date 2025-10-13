# Complete MARC Field Mapping Summary

## Database Schema to MARC21 Field Mapping

This document shows the complete transformation from manga lookup database fields to MARC21 fields with all formatting applied.

## BookInfo Data Structure

```python
@dataclass
class BookInfo:
    series_name: str           # Mapped to 490$a
    volume_number: int         # Mapped to 490$v, 852$h, 090$a
    book_title: str            # Mapped to 245$a
    authors: List[str]         # Mapped to 100$a, 245$c
    msrp_cost: Optional[float] # Mapped to 020$c
    isbn_13: Optional[str]     # Mapped to 001, 020$a
    publisher_name: Optional[str] # Mapped to 264$b
    copyright_year: Optional[int] # Mapped to 008, 264$c
    description: Optional[str] # Mapped to 520$a
    physical_description: Optional[str] # Mapped to 300$a
    genres: List[str]          # Mapped to 500$a, 650$a
    warnings: List[str]        # Mapped to 500$a
```

## Complete Field Mapping Table

| Database Field | MARC Field | Formatting | Indicators | Subfields | Conditional |
|----------------|------------|------------|------------|-----------|-------------|
| **isbn_13** | **001** | `isbn_13.replace("-", "")` | N/A | N/A | Always |
| **isbn_13** | **020** | As-is | `[" ", " "]` | `a`: ISBN | If exists |
| **msrp_cost** | **020** | `f"${msrp_cost:.2f}"` | `[" ", " "]` | `c`: Price | If exists |
| **authors** | **100** | `DataValidator.format_authors_list(authors)` | `["1", " "]` | `a`: Author | If list not empty |
| **book_title** | **245** | As-is | `["1", "0"]` | `a`: Title | Always |
| **authors** | **245** | `DataValidator.format_authors_list(authors)` | `["1", "0"]` | `c`: Responsibility | If list not empty |
| **publisher_name** | **264** | As-is | `[" ", "1"]` | `b`: Publisher | If exists |
| **copyright_year** | **264** | `str(copyright_year)` | `[" ", "1"]` | `c`: Year | If exists |
| **copyright_year** | **008** | Used in positions 07-10 | N/A | N/A | Always |
| **physical_description** | **300** | As-is | `[" ", " "]` | `a`: Physical desc | If exists |
| **N/A** | **300** | `"1 volume (unpaged) : chiefly illustrations ; 19 cm"` | `[" ", " "]` | `a`: Default | If no physical_desc |
| **N/A** | **336** | Fixed for manga | `[" ", " "]` | `a`: "still image"<br>`b`: "sti"<br>`2`: "rdacontent" | Always |
| **N/A** | **337** | Fixed for manga | `[" ", " "]` | `a`: "unmediated"<br>`b`: "n"<br>`2`: "rdamedia" | Always |
| **N/A** | **338** | Fixed for manga | `[" ", " "]` | `a`: "volume"<br>`b`: "nc"<br>`2": "rdacarrier" | Always |
| **series_name** | **490** | As-is | `["1", " "]` | `a`: Series | If exists |
| **volume_number** | **490** | `str(volume_number)` | `["1", " "]` | `v`: Volume | If series exists |
| **description** | **520** | First 500 characters | `[" ", " "]` | `a`: Description | If exists |
| **genres** | **500** | `f"Manga, {', '.join(genres)}"` | `[" ", " "]` | `a`: Material type + genres | If list not empty |
| **genres** | **650** | Each genre individually | `[" ", "0"]` | `a`: Genre<br>`v`: "Comic books, strips, etc." | One per genre |
| **N/A** | **650** | Fixed manga subject | `[" ", "0"]` | `a`: "Manga"<br>`v`: "Comic books, strips, etc." | Always |
| **authors + copyright_year + holding_barcode** | **852** | `generate_call_number()` | `["8", " "]` | `h`: Call number | Always |
| **holding_barcode** | **852** | As provided | `["8", " "]` | `p`: Barcode | Always |
| **N/A** | **852** | Fixed location | `["8", " "]` | `b`: "Main Library"<br>`x`: "Manga collection" | Always |
| **authors + copyright_year + holding_barcode** | **090** | `generate_call_number()` | `[" ", " "]` | `a`: Call number | If authors exist |

## Detailed Formatting Transformations

### Author Name Processing
```python
# Input examples:
# ["Ishida, Sui"] → "Ishida, Sui" (already formatted)
# ["Sui Ishida"] → "Ishida, Sui" (reformatted)
# ["Oda"] → "Oda" (single name)
# ["Kodachi, Ukyo", "Kishimoto, Masashi"] → "Kodachi, Ukyo, Kishimoto, Masashi"

formatted_authors = DataValidator.format_authors_list(book.authors)
```

### Call Number Generation
```python
# Format: "FIC {first 3 letters of author's last name} {copyright year} {holding barcode}"
# From first author, copyright year, and holding barcode
def generate_call_number(book: BookInfo, holding_barcode: str) -> str:
    if not book.authors:
        return f"FIC UNK {book.copyright_year or '0000'} {holding_barcode}"

    first_author = book.authors[0]
    if ", " in first_author:
        last_name = first_author.split(", ")[0]
    else:
        name_parts = first_author.split()
        last_name = name_parts[-1] if name_parts else "UNK"

    author_code = last_name[:3].upper() if len(last_name) >= 3 else last_name.upper()
    year = book.copyright_year or 0000

    return f"FIC {author_code} {year} {holding_barcode}"

# Examples:
# "Ishida, Sui" + 2015 + "T000001" → "FIC ISH 2015 T000001"
# "Oda, Eiichiro" + 2003 + "T000002" → "FIC ODA 2003 T000002"
# "Gotouge, Koyoharu" + 2018 + "T000006" → "FIC GOT 2018 T000006"
```

### 008 Field Construction
```python
# Fixed-length data elements:
field_008 = f"{date_entered}{type_code}{date1}{date2}{country}{illus}{audn}{form}{cont}{gpub} 0 {lang} d"

# Where:
# date_entered = current date ("%y%m%d")
# type_code = "a" (language material)
# date1 = copyright_year or current_year
# date2 = "\\" (no date2)
# country = "xxu" (unknown)
# illus = "    " (not specified)
# audn = " " (unknown audience)
# form = " " (not specified)
# cont = "    " (no contents specified)
# gpub = " " (not government pub)
# lang = "eng" (English)
```

### Holding Barcode Generation
```python
# Sequential barcodes with prefix
holding_barcode = f"{holding_barcode_prefix}{i:06d}"

# Examples:
# "T000001", "T000002", "T000003", etc.
```

### Location
```python
# All books are located at "Main Library"
location = "Main Library"
```

## Field Processing Logic

### Conditional Field Creation
- **ISBN-based fields**: Only created if ISBN exists
- **Author-based fields**: Only created if authors list not empty
- **Publisher/Year fields**: Only created if either exists
- **Series fields**: Only created if series name exists
- **Description fields**: Only created if description exists
- **Genre fields**: Only created if genres list not empty
- **Warning fields**: Only created if warnings list not empty

### Data Validation & Transformation
- **ISBN**: Stripped of hyphens for control number
- **MSRP**: Formatted to 2 decimal places with dollar sign
- **Volume Numbers**: Zero-padded to 3 digits where used
- **Description**: Limited to first 500 characters
- **Copyright Year**: Validated to be between 1900 and current+1

## Complete Example Transformation

### Input BookInfo
```python
BookInfo(
    series_name="Tokyo Ghoul",
    volume_number=1,
    book_title="Tokyo Ghoul (Volume 1)",
    authors=["Ishida, Sui"],
    msrp_cost=12.99,
    isbn_13="9781421580366",
    publisher_name="VIZ Media LLC",
    copyright_year=2015,
    description="In modern-day Tokyo, shy college student Ken Kaneki's life changes forever...",
    physical_description="224 pages : chiefly illustrations ; 19 cm",
    genres=["Horror", "Dark Fantasy", "Seinen", "Supernatural"],
    warnings=["MSRP $12.99 is within expected range"]
)
```

### Output MARC Fields
```marc
001 9781421580366
003 OCoLC
005 20251012023314.0
008 251012a2015\\xxu\\\\\\\\\\0\\eng\\d
020 \\$a9781421580366$c$12.99
040 \\$aOCoLC$beng$cOCoLC$erda
100 1\\$aIshida, Sui
245 10$aTokyo Ghoul (Volume 1)$cIshida, Sui
264 \\1$bVIZ Media LLC$c2015
300 \\$a224 pages : chiefly illustrations ; 19 cm
336 \\$astill image$bsti$2rdacontent
337 \\$aunmediated$bn$2rdamedia
338 \\$avolume$bnc$2rdacarrier
490 1\\$aTokyo Ghoul$v1
520 \\$aIn modern-day Tokyo, shy college student Ken Kaneki's life changes forever...
500 \\$aGENRES: Horror, Dark Fantasy, Seinen, Supernatural
500 \\$aDATA WARNINGS: MSRP $12.99 is within expected range
650 \\0$aHorror$vComic books, strips, etc.
650 \\0$aDark Fantasy$vComic books, strips, etc.
650 \\0$aSeinen$vComic books, strips, etc.
650 \\0$aSupernatural$vComic books, strips, etc.
650 \\0$aManga$vComic books, strips, etc.
852 8\\$bMain Library$hFIC ISH 2015 T000001$pT000001$xManga collection
090 \\$aFIC ISH 2015 T000001
```

## Special Manga-Specific Mappings

1. **Content Types**: Set to "still image" for manga (336 field)
2. **Physical Default**: 19cm format with illustrations for manga
3. **Subject Headings**: All genres get "Comic books, strips, etc." subdivision
4. **Call Numbers**: Format: "FIC {first 3 letters of author's last name} {copyright year} {holding barcode}"
5. **Location**: All books located at "Main Library"
6. **Media Types**: Unmediated, volume carrier for physical manga

This complete mapping ensures that all manga-specific metadata is properly represented in MARC21 format while maintaining compatibility with library systems like Atriuum.