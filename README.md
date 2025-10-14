# Manga Lookup Tool

A Python script that helps you find manga series information by prompting for series name and volume range, correcting series names using DeepSeek API, and displaying comprehensive book information in a beautiful Rich table format.

## Features

- **Series Name Correction**: Uses DeepSeek API to correct and suggest manga series names
- **Volume Range Support**: Search for multiple volumes at once
- **Interactive Rich TUI**: Clickable row interface with navigation controls
- **Comprehensive Book Data**: Includes all fields: series name, volume number, book title, authors, MSRP, ISBN-13, publisher, copyright year, description, physical description, genres
- **Cover Image Integration**: Lazy loading of cover images using Google Books API
- **Title Formatting**: Automatically shifts leading articles to the end ("The Last of the Mohicans" → "Last of the Mohicans, The")
- **Author Formatting**: Formats names as "Last, First M." with comma-separation for multiple authors
- **Advanced State Management**: Tracks API calls, caches responses, and enables session recovery
- **Data Validation**: Validates ISBN-13, MSRP, copyright years with warning system
- **Rate Limiting**: Implements proper rate limiting for DeepSeek API
- **Error Recovery**: Handles partial results and API errors gracefully

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd manga_lookup_tool
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your DeepSeek API key
   ```

## Usage

Run the script:
```bash
python manga_lookup.py
```

The script will:
1. Prompt for manga series name
2. Prompt for volume range (start and end)
3. Use DeepSeek API to correct/suggest series names
4. Ask you to confirm the correct series
5. Fetch comprehensive book data using DeepSeek API for each volume
6. Display results in an interactive table with clickable rows
7. Allow navigation with [n]ext, [p]revious, [r]ow details, [s]ave, [q]uit
8. Show detailed information in pop-up panels
9. Update project state JSON with API call logging

## Interactive Controls

- **[n]**: Next row
- **[p]**: Previous row
- **[r]**: Show row details (full book information)
- **[s]**: Save results to JSON file
- **[q]**: Quit

## Configuration

- **DeepSeek API Key**: Set `DEEPSEEK_API_KEY` in `.env` file
- **Data Source**: Uses DeepSeek API for all book information with "grounded deep research"
- **Cover Images**: Uses keyless Google Books API for lazy loading cover images

## Project Structure

- `manga_lookup.py` - Main implementation script
- `test_comprehensive.py` - Comprehensive test suite
- `requirements.txt` - Python dependencies
- `.env` - Environment variables
- `.env.example` - Environment variables template
- `project_state.json` - Auto-generated state file with API call logging
- `README.md` - User documentation
- `IMPLEMENTATION_SUMMARY.md` - Technical implementation details

## Example Table View

```
Manga Series Results (3 books found)
┌───┬────────┬───────────────┬───────────────┬──────┬───────────────┬───────────────┬──────┬───────────────┬───────────────┬───────────────┐
│ # │ Volume │ Title         │ Authors       │ MSRP │ ISBN-13       │ Publisher     │ Year │ Description   │ Physical      │ Genres        │
├───┼────────┼───────────────┼───────────────┼──────┼───────────────┼───────────────┼──────┼───────────────┼───────────────┼───────────────┤
│ → │ 1      │ One Piece (V... │ Oda, Eiichiro │ $9.99│ 9781569319... │ VIZ Media ... │ 2003 │ Monkey D. L... │ 208 pages,... │ Shonen, Adv... │
│   │ 2      │ One Piece (V... │ Oda, Eiichiro │ $9.99│ 9781569319... │ VIZ Media ... │ 2004 │ The Straw H... │ 208 pages,... │ Shonen, Adv... │
│   │ 3      │ One Piece (V... │ Oda, Eiichiro │ $9.99│ 9781421536... │ VIZ Media ... │ 2005 │ Luffy and h... │ 216 pages,... │ Shonen, Adv... │
└───┴────────┴───────────────┴───────────────┴──────┴───────────────┴───────────────┴──────┴───────────────┴───────────────┴───────────────┘
Controls: [q]uit, [n]ext, [p]revious, [r]ow details, [s]ave
```

## Data Sources

- **All Information**: DeepSeek API with "grounded deep research"
- **ISBN Validation**: isbntools library for ISBN-13 validation and metadata

## License

MIT License