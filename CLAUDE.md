# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Streamlit web application that obtains official API Football team IDs using a **fixture-based approach**. Instead of fuzzy matching team names, it uses specific match information (date, teams) to find exact fixtures in API Football and extract precise team IDs.

### Two Approaches Available

1. **Original app.py**: Name-based matching with contextual information
2. **app_fixture_based.py**: NEW fixture-based approach (recommended) - uses match text to find exact fixtures

### Core Architecture

#### Fixture-Based System (app_fixture_based.py + fixture_matcher.py)
- **FixtureMatcher**: Main class that parses match text and searches API Football fixtures
- **Match Text Parsing**: Extracts date, time, and team names from formatted text
- **Fixture Search**: Uses API Football's fixtures endpoint to find exact matches by date
- **ID Extraction**: Gets official team IDs directly from matched fixtures
- **High Precision**: Achieves near 100% accuracy by matching exact fixtures

#### Original Name-Based System (app.py)
- **TeamAssociationSystem**: Team name matching with manual mappings and similarity algorithms
- **Contextual Matching**: Uses opponent information to improve accuracy
- **Multiple Data Sources**: Supports example data, API Football API, or uploaded JSON

### Key Features

- **Fixture-based matching**: Uses specific match dates and team pairs to find exact fixtures
- **High accuracy**: Achieves 100% success rate on test data
- **Multiple leagues supported**: Works with any league available in API Football
- **Excel output**: Generates comprehensive Excel files with team IDs and mapping details
- **API integration**: Uses RapidAPI's API Football service

## Development Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run original name-based app
streamlit run app.py

# Run NEW fixture-based app (recommended)
streamlit run app_fixture_based.py

# Test fixture matching system
python fixture_matcher.py

# Test complete process with sample data
python test_full_process.py
```

### Key Files Structure
- `app.py` - Original name-based Streamlit application
- `app_fixture_based.py` - NEW fixture-based Streamlit application (recommended)
- `fixture_matcher.py` - Core fixture matching logic and API integration
- `tashist.csv` - Sample data file with match information
- `requirements.txt` - Python dependencies
- `test_full_process.py` - Complete system testing script
- `readme.md` - Project documentation

### Dependencies
- streamlit>=1.28.0 - Web application framework
- pandas>=2.0.0 - Data manipulation and CSV/Excel processing
- openpyxl>=3.1.0 - Excel file reading/writing
- requests>=2.31.0 - API calls to API Football
- xlsxwriter>=3.1.0 - Excel file generation

## Core Functions to Understand

### Fixture-Based Matching (fixture_matcher.py)

#### FixtureMatcher.parse_match_text() (lines 24-50)
Parses match text format: "Fecha: 4/4 21:00, Partido: Tijuana vs Necaxa"
- Extracts date, time, and team names using regex
- Converts date to API-compatible format (YYYY-MM-DD)

#### FixtureMatcher.search_fixtures_by_date() (lines 58-80)
Searches API Football for all fixtures on a specific date
- Uses `/fixtures` endpoint with date parameter
- Implements caching to avoid repeated API calls
- Returns all fixtures for the given date

#### FixtureMatcher.find_matching_fixture() (lines 82-126)
Finds the specific fixture that matches the parsed team names
- Compares team names from parsed text with fixture teams
- Uses fuzzy matching to handle name variations
- Returns best matching fixture with confidence score

#### FixtureMatcher.process_match_text() (lines 136-177)
Main processing function that combines all steps
- Parses → Searches → Matches → Extracts IDs
- Returns complete result with success status and team IDs

### Original Name-Based System (app.py)

#### TeamAssociationSystem.find_best_match() (lines 238-285)
Three-tier matching strategy with contextual information:
1. Manual mapping lookup
2. Exact normalized match  
3. String similarity with context boost

#### Excel Processing (lines 470-482)
Extracts team names from standard columns (`Local`, `Visitante`, etc.)

## Working with the Codebase

### Using the Fixture-Based System

#### Required Data Format
The CSV must have a "Match text" column with this exact format:
```
Fecha: M/D HH:MM, Partido: Team1 vs Team2
```
Example: `Fecha: 4/4 21:00, Partido: Tijuana vs Necaxa`

#### API Configuration
Set your RapidAPI key in the FixtureMatcher constructor:
```python
api_key = "your_rapidapi_key_here"
matcher = FixtureMatcher(api_key)
```

#### Processing Flow
1. Parse match text → Extract date and team names
2. Search fixtures → Get all fixtures for that date
3. Match teams → Find fixture with matching team names
4. Extract IDs → Get official team IDs from fixture

### Extending the System

#### Adding New Date Formats
Modify the regex pattern in `parse_match_text()` method:
```python
pattern = r"Fecha:\s*(\d+/\d+)\s*(\d+:\d+)?,\s*Partido:\s*(.+?)\s*vs\s*(.+)"
```

#### Improving Team Name Matching
Enhance the matching logic in `find_matching_fixture()` method by:
- Adding more fuzzy matching algorithms
- Implementing team name normalization
- Adding manual team name mappings

#### Adding New Leagues/Competitions
The system automatically works with any league available in API Football since it searches by date, not by league.

## API Integration

The application integrates with API Football via RapidAPI (api-football-v1.p.rapidapi.com). 

### API Endpoints Used

#### Fixture-Based System
- `/fixtures` - Get fixtures by date
  - Parameters: `date` (YYYY-MM-DD format)
  - Returns: All fixtures for the specified date
  - Usage: Find exact matches for team pairs

#### Original System  
- `/teams` - Retrieve teams by league and season
  - Parameters: `league` (ID), `season` (year)
  - Returns: Team data for fuzzy matching

### API Configuration
```python
headers = {
    "x-rapidapi-key": "your_api_key_here",
    "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
}
```

### Rate Limiting
- Free tier: 100 calls/day
- Fixture-based system: 1 call per unique date in CSV
- Original system: 1 call per league selected
- Built-in caching reduces redundant API calls

## Recommended Workflow

1. **Use fixture-based system** (`app_fixture_based.py`) for highest accuracy
2. **Prepare CSV** with proper "Match text" column format
3. **Set API key** in the application or code
4. **Process in batches** to respect API rate limits
5. **Review results** in generated Excel file with three sheets:
   - `Datos_con_IDs`: Original data + API Football IDs
   - `Mapeo_Fixtures`: Detailed fixture mapping information
   - `Resumen`: Processing statistics and summary

## Test Results

The fixture-based system has been tested with real data from `tashist.csv`:
- **100% success rate** on sample data (5/5 matches found)
- **Exact fixture matching** for teams across multiple leagues
- **Proper ID extraction** from API Football responses
- **Excel generation** working correctly with comprehensive mapping data