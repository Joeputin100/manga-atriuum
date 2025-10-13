# MARC Export Documentation

## Overview

The Manga Lookup Tool now includes comprehensive MARC21 export functionality for creating bibliographic and holding records compatible with library systems like Atriuum.

## Features

### 1. MARC21 Record Creation
- **Bibliographic Records**: Complete MARC21 records with all standard fields
- **Holding Information**: Integrated 852 fields with barcodes and location data
- **Atriuum Compatibility**: Follows Atriuum MARC schema requirements
- **Multiple Formats**: Supports both single records and batch exports

### 2. Field Mapping

#### Control Fields
- **001**: Control Number (ISBN or generated ID)
- **003**: Control Number Identifier (OCoLC)
- **005**: Date/Time of Latest Transaction
- **008**: Fixed-Length Data Elements

#### Data Fields
- **020**: ISBN with price information
- **040**: Cataloging Source (OCoLC)
- **100**: Main Entry - Personal Name (Author)
- **245**: Title Statement with indicators
- **264**: Publication Information
- **300**: Physical Description
- **336-338**: RDA Content, Media, and Carrier Types
- **490**: Series Statement
- **500**: General Notes (genres, warnings)
- **520**: Summary/Description
- **650**: Subject Headings (genres as subjects)
- **852**: Location/Holding Information
- **090**: Local Call Number (LC-style)

### 3. Special Manga Features

- **Genre Mapping**: Automatically converts manga genres to subject headings
- **Physical Description**: Default manga format (19cm, illustrations)
- **Content Types**: Properly set for manga (still image, unmediated, volume)
- **Call Numbers**: Generated LC-style call numbers for manga

## Usage

### Interactive Mode
In the text-based list interface, press `m` to export current results to MARC format:

```
Controls: [number] to view details, [q]uit, [s]ave JSON, [m]arc export
```

### Programmatic Usage
```python
from marc_exporter import export_books_to_marc

# Export list of BookInfo objects
export_books_to_marc(books, "output.mrc", "B")
```

### Test Records
Run `test_marc_export.py` to generate a sample MARC file with 10 popular manga volumes:

```bash
python3 test_marc_export.py
```

## Atriuum Import Instructions

1. **Prepare File**: Generate MARC file using the tool
2. **Open Atriuum**: Navigate to Cataloging → Import MARC Records
3. **Select File**: Choose the generated `.mrc` file
4. **Field Mapping**: Map according to your library's configuration
5. **Test Import**: Start with small batches to verify mapping

### Key Fields for Atriuum
- **852 Field**: Contains holding information (barcode, location, call number)
- **001 Field**: Used as bibliographic record identifier
- **020 Field**: ISBN for matching existing records

## File Format

- **Extension**: `.mrc` (MARC21 binary format)
- **Encoding**: UTF-8
- **Records**: Each record contains both bibliographic and holding information
- **Barcodes**: Sequential barcodes with configurable prefix

## Dependencies

- `pymarc`: Python MARC library for record creation
- Installed automatically when needed

## Test Files Generated

1. **test_manga_record.mrc**: Single test record
2. **test_manga_collection.mrc**: 10-volume test collection
3. **manga_marc_*.mrc**: Timestamped exports from interactive mode

## Troubleshooting

### Common Issues
1. **Import Errors**: Check 008 field format and indicator values
2. **Missing Holdings**: Verify 852 field mapping in Atriuum
3. **Character Encoding**: Ensure UTF-8 encoding for special characters

### Field Validation
- All required MARC21 fields are populated
- Indicators set according to MARC21 standards
- Subfields follow RDA and local practice guidelines

## Sample Record Structure

```marc
001 9781421580366
003 OCoLC
005 20251012005943.0
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
650 \\0$aHorror$vComic books, strips, etc.
650 \\0$aManga$vComic books, strips, etc.
852 8\\$bs$hGN 001$pT000001$xManga collection
090 \\$aPN6790.J34 ISH 001
```

This documentation provides everything needed to successfully export manga records to MARC format and import them into Atriuum or other library systems.