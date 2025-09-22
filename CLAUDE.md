# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp env.example .env
# Edit .env file to set MOLIT_API_KEY and other configurations
```

### Running the Application
```bash
# Start the web server (main development command)
python main.py

# Access the application at http://localhost:8080
```

### Environment Configuration
- Create `.env` file from `env.example` template
- **Required**: `MOLIT_API_KEY` - API key from Korea Ministry of Land, Infrastructure and Transport
- Optional: Flask server settings (host, port, debug mode)
- Optional: API request settings (delay, timeout, retries)

## Architecture

### Core Components

**Main Application Flow**: `main.py` → `src/web_app.py` (Flask app) → `src/molit_api.py` (API client) + `src/database.py` (data storage)

**Key Classes**:
- `ApartmentTrackerApp` (src/web_app.py): Main Flask web application with routes for search, favorites, and dashboard
- `MolitRealEstateAPI` (src/molit_api.py): API client for Korea's Ministry of Land real estate data with built-in regional hierarchy
- `ApartmentDatabase` (src/database.py): SQLite database manager for favorites and caching system

### Data Flow Architecture

1. **Regional Hierarchy**: Built-in mapping from city/province → district → legal dong code (법정동코드)
2. **API Integration**: Calls Ministry of Land API with proper rate limiting and error handling
3. **Smart Caching**: 24-hour cache system for search results to minimize API calls
4. **Three-tier Data View**: Results organized by legal dong (법정동별), monthly (월별), and apartment (아파트별) tabs

### Database Schema

**Primary Tables**:
- `favorite_apartments`: User's favorite apartment complexes with metadata
- `apartment_transactions`: Real estate transaction history with price tracking
- `search_cache`: API response caching with 24-hour TTL
- `price_history`: Monthly price trend tracking for favorites dashboard

### UI Components

**Template Structure**: Bootstrap 5-based responsive design with:
- Dashboard (`index.html`): Favorites overview with price change indicators
- Search (`search.html`): Three-tab system with advanced filtering
- Apartment Detail (`apartment_detail.html`): Individual complex analysis with Chart.js
- Favorites Management (`favorites.html`): Watchlist management

### Regional Code System

The application uses Korea's standard legal dong codes (법정동코드) with a hierarchical structure:
- Level 1: City/Province (시/도)
- Level 2: District/County (군/구)
- Level 3: Legal dong (법정동)

Built-in support for all 17 Korean administrative divisions including special cities, metropolitan cities, special autonomous provinces, and regular provinces.

## Key Features

### Performance Optimizations
- **Smart Caching**: Search results cached for 24 hours in SQLite
- **API Rate Limiting**: Configurable delays between API calls
- **Database Indexing**: Optimized queries for favorites and transaction history

### Data Analysis Tools
- **Three-tab System**: Systematic data classification by region, time, and property
- **Advanced Filtering**: Cross-tab filtering capabilities
- **Price Trend Analysis**: Month-over-month price change tracking with visual indicators
- **CSV Export**: Transaction data export functionality

## Technical Notes

### API Integration
- Uses Korea Ministry of Land official real estate transaction API
- Requires valid API key from data.go.kr
- Built-in retry logic and error handling
- Supports date range and regional filtering

### Database Design
- SQLite for simplicity and portability
- Automatic schema migration and table creation
- Foreign key constraints for data integrity
- Optimized for read-heavy workloads (dashboard and search)

### Security Considerations
- Environment-based configuration management
- No hardcoded credentials
- CSRF protection via Flask's built-in security
- Production-ready session management settings

## Development Guidelines

### Implementation Standards
- **IMPORTANT**: All new features and modifications must follow the requirements specified in `rules.md`
- `rules.md` contains the official program specifications and requirements that override any other documentation
- Before implementing any new feature, review `rules.md` to ensure compliance with the established requirements
- All new implementations should be documented in the "신규구현사항 (추가)" section of `rules.md`

### Feature Development Process
1. Review `rules.md` for relevant requirements before starting development
2. Implement features according to the specifications in `rules.md`
3. Update the "신규구현사항 (추가)" section in `rules.md` with details of new implementations
4. Ensure all features align with the program's core purpose as defined in `rules.md`