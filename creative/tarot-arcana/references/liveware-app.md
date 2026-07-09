# Liveware Web App — API Reference

## API Endpoints

### `POST /api/interpret`

Submits card/question data to the Hermes API Server for interpretation. The API-server agent uses the tarot-arcana skill to analyze and return the reading.

### `GET /api/deck`

Serves the full 78-card tarot deck data for the frontend.

## Readings Storage

Readings are saved to `~/tarot-readings/` with an `index.json` history and individual markdown files.
