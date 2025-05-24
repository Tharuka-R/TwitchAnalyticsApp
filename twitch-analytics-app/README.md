# Twitch Analytics Application

## Overview
The Twitch Analytics Application is designed to help analyze and report viewer count data for the Twitch streamer "Da1lyVitamin." This application allows users to insert viewer data and generate performance reports in PDF format, providing insights into viewers, followers, subscribers, bit donors, gift subbers, and overall donors on a daily and monthly basis.

## Features
- Insert viewer count data into the database.
- Generate performance reports in PDF format.
- Analyze daily and monthly performance metrics.
- Track various data points including viewers, followers, subscribers, and donations.

## Project Structure
```
twitch-analytics-app
├── src
│   ├── app.py                # Entry point of the application
│   ├── database
│   │   └── models.py         # Database models for data storage
│   ├── routes
│   │   └── analytics.py       # Route handlers for data insertion and report generation
│   ├── services
│   │   ├── data_insertion.py  # Logic for inserting data into the database
│   │   ├── report_generation.py# Handles PDF report generation
│   │   └── analysis.py        # Functions for data analysis
│   ├── utils
│   │   └── pdf_utils.py       # Utility functions for PDF creation
│   └── types
│       └── __init__.py       # Custom types or interfaces
├── requirements.txt           # Project dependencies
└── README.md                  # Project documentation
```

## Setup Instructions
1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```
   cd twitch-analytics-app
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
- Start the application by running:
  ```
  python src/app.py
  ```
- Use the API endpoints defined in `src/routes/analytics.py` to insert data and generate reports.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License.