# MARC Field Mapping Analysis

## Database Schema to MARC21 Field Mapping

This document shows exactly how fields from the manga lookup database (`BookInfo` class) are mapped to MARC21 fields and what formatting transformations are applied.

## BookInfo Data Structure

```python
@dataclass
class BookInfo:
    series_name: str
    volume_number: int
    book_title: str
    authors: List[str]
    msrp_cost: Optional[float]
    isbn_13: Optional[str]
    publisher_name: Optional[str]
    copyright_year: Optional[int]
    description: Optional[str]
    physical_description: Optional[str]
    genres: List[str]
    warnings: List[str]
```

## Field-by-Field Mapping

### Control Fields

| MARC Field | Database Field | Formatting | Indicators | Notes |
|------------|----------------|------------|------------|-------|
| **001** | `isbn_13` or `volume_number` | `isbn_13.replace("-", "")` or `f"M{volume_number:03d}"` | N/A | Control number from ISBN or generated ID |
| **003** | Generated | `"OCoLC"` | N/A | Fixed cataloging source |
| **005** | Generated | Current timestamp `"%Y%m%d%H%M%S.0"` | N/A | Last modification date |
| **008** | Multiple fields | Complex fixed-length format | N/A | See detailed breakdown below |

### 008 Field Breakdown

```python
# Positions in 008 field:
# 00-05: Date entered (current date: "%y%m%d")
# 06: Type code ("a" = Language material)
# 07-10: Date1 (copyright_year or current_year)
# 11-14: Date2 ("\\" = No date2)
# 15-17: Country ("xxu" = Unknown country)
# 18-21: Illustrations ("    " = Not specified)
# 22: Target audience (" " = Unknown)
# 23: Form (" " = Not specified)
# 24-27: Nature of contents ("    " = Not specified)
# 28: Govt pub (" " = Not government publication)
# 29-34: Various flags (" 0 " = Default values)
# 35-37: Biography ("   " = Not specified)
# 38: Language ("eng" = English)
# 39: Modified record ("d" = Default)
```

### Data Fields

| MARC Field | Database Field | Formatting | Indicators | Subfields |
|------------|----------------|------------|------------|-----------|
| **020** | `isbn_13` + `msrp_cost` | ISBN as-is, MSRP as `f"${msrp_cost:.2f}"` | `[" ", " "]` | `a`: ISBN<br>`c`: Price |
| **040** | Generated | Fixed cataloging source | `[" ", " "]` | `a`: "OCoLC"<br>`b`: "eng"<br>`c`: "OCoLC"<br>`e`: "rda" |
| **100** | `authors` | `DataValidator.format_authors_list(authors)` | `["1", " "]` | `a`: Formatted author name |
| **245** | `book_title` + `authors` | Title as-is, authors in responsibility | `["1", "0"]` | `a`: Title<br>`c`: Author (if exists) |
| **264** | `publisher_name` + `copyright_year` | Publisher as-is, year as string | `[" ", "1"]` | `b`: Publisher<br>`c`: Year |
| **300** | `physical_description` | As-is or default manga format | `[" ", " "]` | `a`: Physical description |
| **336** | Generated | Fixed for manga | `[" ", " "]` | `a`: "still image"<br>`b`: "sti"<br>`2`: "rdacontent" |
| **337** | Generated | Fixed for manga | `[" ", " "]` | `a`: "unmediated"<br>`b`: "n"<br>`2`: "rdamedia" |
| **338** | Generated | Fixed for manga | `[" ", " "]` | `a`: "volume"<br>`b`: "nc"<br>`2`: "rdacarrier" |
| **490** | `series_name` + `volume_number` | Series as-is, volume as string | `["1", " "]` | `a`: Series name<br>`v`: Volume number |
| **520** | `description` | First 500 characters | `[" ", " "]` | `a`: Description |
| **500** | `genres` | `f"Manga, {', '.join(genres)}"` | `[" ", " "]` | `a`: Material type + genres |
| **650** | `genres` | Each genre as subject heading | `[" ", "0"]` | `a`: Genre<br>`v`: "Comic books, strips, etc." |
| **650** | Generated | Fixed manga subject | `[" ", "0"]` | `a`: "Manga"<br>`v`: "Comic books, strips, etc." |
| **852** | `authors` + `copyright_year` + holding_barcode | Generated call number | `["8", " "]` | `b`: "Main Library"<br>`h`: `generate_call_number()`<br>`p`: Barcode<br>`x`: "Manga collection" |
| **090** | `authors` + `copyright_year` + holding_barcode | Generated call number | `[" ", " "]` | `a`: `generate_call_number()` |

## Formatting Transformations

### Author Name Formatting
```python
# Input: ["Ishida, Sui"] or ["Sui Ishida"]
# Output: "Ishida, Sui" (always in "Last, First" format)
formatted_authors = DataValidator.format_authors_list(book.authors)
```

### Call Number Generation
```python
# Format: "FIC {first 3 letters of author's last name} {copyright year} {holding barcode}"
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
```

### Physical Description Default
```python
# If physical_description is None:
default_physical = "1 volume (unpaged) : chiefly illustrations ; 19 cm"
```

### Holding Barcode Generation
```python
# Sequential barcodes with prefix
holding_barcode = f"{holding_barcode_prefix}{i:06d}"
# Example: "T000001", "T000002", etc.
```

## Field Processing Logic

### Conditional Field Creation
- **020**: Only created if `isbn_13` exists
- **100**: Only created if `authors` list is not empty
- **264**: Only created if `publisher_name` or `copyright_year` exists
- **490**: Only created if `series_name` exists
- **520**: Only created if `description` exists
- **500 (genres)**: Only created if `genres` list is not empty
- **500 (warnings)**: Only created if `warnings` list is not empty
- **650 (genres)**: One field per genre in `genres` list
- **090**: Only created if `authors` list is not empty

### Data Validation
- **ISBN**: Used as-is, no validation
- **MSRP**: Formatted to 2 decimal places with dollar sign
- **Copyright Year**: Used directly if exists
- **Volume Number**: Zero-padded to 3 digits where used
- **Description**: Limited to first 500 characters

## Example Transformation

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
- **001**: `9781421580366` (from ISBN)
- **020**: `$a9781421580366$c$12.99` (ISBN + price)
- **100**: `1$a"Ishida, Sui"` (author)
- **245**: `10$a"Tokyo Ghoul (Volume 1)"$c"Ishida, Sui"` (title + author)
- **264**: ` 1$b"VIZ Media LLC"$c"2015"` (publisher + year)
- **300**: `  $a"224 pages : chiefly illustrations ; 19 cm"` (physical)
- **490**: `1 $a"Tokyo Ghoul"$v"1"` (series + volume)
- **520**: `  $a"In modern-day Tokyo..."` (description)
- **500**: `  $a"GENRES: Horror, Dark Fantasy, Seinen, Supernatural"` (genres)
- **500**: `  $a"DATA WARNINGS: MSRP $12.99 is within expected range"` (warnings)
- **650**: Multiple fields for each genre
- **852**: `8 $b"s"$h"GN 001"$p"T000001"$x"Manga collection"` (holding)
- **090**: `  $a"PN6790.J34 ISH 001"` (call number)

## Special Manga Considerations

1. **Content Types**: Set to "still image" for manga (336 field)
2. **Physical Default**: 19cm format with illustrations
3. **Subject Headings**: All genres get "Comic books, strips, etc." subdivision
4. **Call Numbers**: Use PN6790.J34 (Japanese comics) classification
5. **Location**: Default to "Manga collection" in stacks

This mapping ensures that all manga-specific metadata is properly represented in MARC21 format while maintaining compatibility with library systems like Atriuum.