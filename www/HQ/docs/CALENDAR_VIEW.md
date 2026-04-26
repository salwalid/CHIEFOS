# Calendar View Documentation

## Overview
The Calendar View is a dynamic web-based dashboard part of the HQ interface, designed to display a rolling 7-day schedule of events and tasks.

## 7-Day Grid Logic
- **Rolling Window**: The grid calculates the current date and renders the next 6 days (total 7 days including today).
- **Responsive Layout**: Uses CSS Grid for a flexible layout that adapts to mobile and desktop screens.
- **Dynamic Updates**: Each cell in the grid corresponds to a day, populated with data fetched from `schedule.json`.

## schedule.json Structure
The data source for the calendar is a JSON file structured as follows:
```json
{
  "events": [
    {
      "date": "YYYY-MM-DD",
      "time": "HH:MM",
      "title": "Event Title",
      "type": "work|personal|reminder",
      "description": "Optional details"
    }
  ]
}
```

## update_calendar.py Workflow
The `update_calendar.py` script manages the synchronization of data:
1. **Fetch**: Pulls data from the primary Google Calendar/Task APIs or local database.
2. **Transform**: Formats raw event data into the standardized `schedule.json` schema.
3. **Validate**: Ensures date strings and required fields are present.
4. **Deploy**: Overwrites the active `www/HQ/data/schedule.json` used by the frontend.

## Deployment
- **Path**: `$CHIEFOS_HOME/www/HQ/`
- **Frontend**: `calendar.html`, `calendar.css`, `calendar.js`
- **Backend**: `update_calendar.py` (triggered via cron or webhook)
