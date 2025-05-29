# 🏥 Hospital Recommendation AI

This project is a prototype web service that uses the **ChatGPT API** to recommend hospitals based on a user's natural language symptom input. Hospital data is retrieved from a **PostgreSQL database (NEON)**.

## 📦 Environment Setup

1. Requires Python 3.8 or higher.
2. Create a `.env` file in the root directory with the following variables:

```env
DATABASE_URL=your_postgresql_connection_string
OPENAI_API_KEY=your_openai_api_key
