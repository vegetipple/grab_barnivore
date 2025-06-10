# Barnivore Data Scraper

A Python web scraper that downloads vegan beer, wine, and spirits data from [Barnivore.com](https://www.barnivore.com) and stores it in a SQLite database for offline access and analysis.

## About Barnivore

[Barnivore](https://www.barnivore.com) is an invaluable resource for vegans, providing a comprehensive database of alcoholic beverages and their vegan status. The site is maintained by volunteers who research and verify whether companies use animal-derived ingredients or processing methods in their products.

**We are deeply grateful to Barnivore and its contributors** for:
- Curating this essential database through dedicated research
- Making their data accessible via a public API
- Providing an invaluable service to the vegan community

This scraper is intended to complement Barnivore's work by enabling offline access and bulk analysis of their data. Please consider [supporting Barnivore](https://www.barnivore.com/donate) for their ongoing efforts.

## What This Scraper Does

The scraper fetches data from Barnivore's JSON API and stores it locally in a SQLite database:

1. **Retrieves company listings** from beer, wine, and liquor endpoints
2. **Fetches detailed company information** including contact details and vegan status
3. **Downloads product data** for each company with individual vegan classifications
4. **Stores everything in SQLite** with proper relational structure

## Database Contents

The resulting database contains three main tables:

- **Companies**: Contact information, location, and overall vegan status
- **Products**: Individual beverages with their vegan classification
- **Stats**: Scraping metadata and timestamps

Vegan status is indicated by the `redyellowgreen` field:
- `green`: Vegan-friendly
- `yellow`: May not be vegan (unclear/mixed)
- `red`: Not vegan

## Usage

### Basic Usage

Run the scraper with default settings:
```bash
python3 barnivore_scraper.py
```

### Custom Database and Rate Limiting

```bash
python3 barnivore_scraper.py --db my_barnivore.db --delay 2.0
```

### Check Database Statistics

```bash
python3 barnivore_scraper.py --stats-only --db barnivore_20250106.db
```

## Requirements

- Python 3.7+
- `requests` library

Install dependencies:
```bash
pip install requests
```

## Example Queries

Once you have a database, you can query it with any SQLite client:

### Find all vegan companies
```sql
SELECT companyname, city, state, country 
FROM company 
WHERE redyellowgreen = 'green';
```

### Search for vegan beers
```sql
SELECT p.productname, c.companyname, c.city, c.state
FROM product p 
JOIN company c ON p.companyid = c.id 
WHERE p.redyellowgreen = 'green' 
  AND p.boozetype = 'beer'
ORDER BY c.companyname, p.productname;
```

### Count products by type and vegan status
```sql
SELECT boozetype, redyellowgreen, COUNT(*) as count
FROM product 
GROUP BY boozetype, redyellowgreen
ORDER BY boozetype, redyellowgreen;
```

## GitHub Action

This repository includes a GitHub Action that automatically runs the scraper and creates releases with the database file. See `.github/workflows/scrape-and-release.yml` for details.

## Rate Limiting and Ethics

The scraper includes built-in rate limiting (1 second delay by default) to be respectful of Barnivore's servers. Please:

- Use reasonable delays between requests
- Don't run the scraper excessively 
- Consider the load on Barnivore's infrastructure
- Support Barnivore financially if you find their data valuable

## License

This scraper is provided as-is for educational and research purposes. The data it collects belongs to Barnivore and is subject to their terms of use.

## Disclaimer

This tool is not affiliated with or endorsed by Barnivore. Always verify vegan status directly with manufacturers or Barnivore.com for the most current information, as product formulations and company policies can change.