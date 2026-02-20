# Smart Travel Companion – Context-Aware AI Layer

This package contains the Smart Travel Companion, a Context-Aware AI Layer prototype built with FastAPI, LangGraph, and Google Gemini 2.5 Flash.

## Overview

The AI assistant acts as a comprehensive travel agent guiding users seamlessly across multiple travel services such as Flights and Hotels. It strictly tracks constraints, stores session-specific state, supports mid-flow context switching, and manages proper re-prompts and invalidations.

## Prerequisites

- Python 3.10+
- A Google API Key (`AIzaSyC2nfiDKQy3NnXVRitZyK0K7XZnNaHiHvQ` provided in `main.py` directly for assessment ease)

## Installation

1. Create a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. Start the FastAPI server:
   ```bash
   python main.py
   ```
   Alternatively, use uvicorn directly:
   ```bash
   uvicorn main:app --reload
   ```

2. The server will run at `http://localhost:8000`. 
   - Interactive API Docs are available at `http://localhost:8000/docs`.

### Testing via CURL or Postman

You can easily interact with the chat endpoint:

```bash
curl -X 'POST' \
  'http://localhost:8000/chat' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "session_id": "user123",
  "message": "I want to book a flight from New York to London for December 15th."
}'
```

### Try Mid-Conversation Context Switching

Send follow-up requests with the same `session_id` to switch context or ask constraints, e.g.,
1. "Wait, I need a hotel in London first."
2. "Are there any hotels with free WiFi?"
3. "Ok, I will go with Grand Plaza."
4. "Let's go back to the flight."
