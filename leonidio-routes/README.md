# Leonidio Climbing Routes Scraper

This scraper extracts information about all climbing crags and routes from [climbinleonidio.com](https://climbinleonidio.com/crags/).

## Features

- Scrapes all 38+ crags from Leonidio climbing area
- Extracts detailed information for each crag and route
- Exports data to structured CSV files
- Respectful scraping with delays between requests
- Comprehensive logging

## Output Files

### `leonidio_crags.csv`
Contains information about each climbing crag:
- `crag_number`: Numerical identifier (1-38+)
- `crag_name`: Name of the climbing area
- `description`: Full description text from the site
- `route_count`: Total number of routes in the crag
- `best_period`: Recommended climbing season
- `busy_level`: Crowding level (1-4 dots)
- `exposure`: Cardinal directions the crag faces
- `shade`: Shade conditions and timing
- `elevation_m`: Elevation in meters (when available)
- `crag_url`: Direct URL to the crag page

### `leonidio_routes.csv`
Contains information about individual climbing routes:
- `crag_number`: Parent crag identifier
- `crag_name`: Parent crag name
- `route_number`: Route number within the crag
- `route_name`: Name of the climbing route
- `grade`: Climbing grade (French system, e.g., 6a, 7b+, 8c)
- `length_m`: Route length in meters
- `route_url`: Direct URL to the route page

## Installation

1. Install Python 3.7+ if not already installed
2. Install required packages:

```bash
pip install -r requirements.txt
```

## Usage

Run the scraper:

```bash
python leonidio_scraper.py
```

The script will:
1. Fetch the main crags page
2. Extract basic information for each crag
3. Visit each crag's individual page for detailed information
4. Extract all routes for each crag
5. Save everything to CSV files

## Expected Output

The scraper should find:
- 38+ climbing crags
- 1000+ individual climbing routes
- Complete metadata for each crag and route

## Data Quality Notes

- The scraper handles various text formatting inconsistencies on the source site
- Some route information may be incomplete if the source data is irregular
- The script includes robust error handling and will continue if individual pages fail
- All text is preserved in UTF-8 encoding to handle special characters

## Sample Data

### Sample Crag Entry:
```csv
crag_number,crag_name,description,route_count,best_period,busy_level,exposure,shade,elevation_m,crag_url
01,Nifada,"At 800m elevation, a colorful cave with hardcore sport climbing...",62,"April – November",2,"NE","All day;until 16:00 (left)",800,"http://climbinleonidio.com/view/?crag=Nifada"
```

### Sample Route Entry:
```csv
crag_number,crag_name,route_number,route_name,grade,length_m,route_url
01,Nifada,05,"De puta madre",8c,30,"https://climbinleonidio.com/route/de-puta-madre-16/"
```

## Technical Details

- Uses BeautifulSoup for HTML parsing
- Implements respectful scraping with 1-second delays
- Includes comprehensive logging for debugging
- Handles URL encoding and special characters
- Robust regex patterns for parsing route information

## Contributing

Feel free to submit issues or improvements to the parsing logic if you notice data quality issues.