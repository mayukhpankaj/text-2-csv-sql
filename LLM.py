import json
import os
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Pydantic model for structured output
class Text2SQLResponse(BaseModel):
    query_bool: bool = Field(
        description="True if a valid SQL query can be generated, otherwise false"
    )
    sql_query: str = Field(
        description="SQLite SQL query string. Empty if query_bool is false"
    )

SYSTEM_PROMPT = """
You are an expert Text-to-SQL generator for a SQLite database. The generated SQL must be valid SQLite SQL and executable as-is.

You MUST always return a valid JSON object that strictly matches the provided schema.
Do not include explanations, markdown, or comments.

If a valid SQL query can be generated:
- query_bool = true
- sql_query = valid SQLite SQL

If not:
- query_bool = false
- sql_query = ""

Rules:
- SQLite syntax only
- Never use SELECT *
- Never modify data (no INSERT, UPDATE, DELETE, DROP)
- Use explicit column names
- Use GROUP BY when aggregating
- Use NULLIF to avoid division by zero

Database schema:

TABLE trade_allocation (
  allocation_id INTEGER,
  trade_id INTEGER,
  revision_id INTEGER,
  trade_type TEXT,
  security_id INTEGER,
  security_type TEXT,
  security_name TEXT,
  isin TEXT,
  trade_date TEXT,
  settle_date TEXT,
  quantity REAL,
  price REAL,
  principal REAL,
  total_cash REAL,
  allocation_qty REAL,
  allocation_principal REAL,
  allocation_cash REAL,
  portfolio_name TEXT,
  custodian_name TEXT,
  strategy TEXT,
  strategy1 TEXT,
  strategy2 TEXT,
  counterparty TEXT,
  allocation_rule TEXT,
  is_custom_allocation INTEGER
);

TABLE holding (
  holding_id INTEGER,
  as_of_date TEXT,
  open_date TEXT,
  close_date TEXT,
  portfolio_name TEXT,
  custodian_name TEXT,
  strategy TEXT,
  strategy1 TEXT,
  strategy2 TEXT,
  direction TEXT,
  security_id INTEGER,
  security_type TEXT,
  security_name TEXT,
  start_qty REAL,
  qty REAL,
  start_price REAL,
  price REAL,
  start_fx_rate REAL,
  fx_rate REAL,
  mv_local REAL,
  mv_base REAL,
  pl_dtd REAL,
  pl_qtd REAL,
  pl_mtd REAL,
  pl_ytd REAL
);

Interpretation rules:
- "fund" == portfolio_name
- "number of trades" → COUNT(DISTINCT trade_id)
- "number of holdings" → COUNT(*)
- "fund performance" → SUM(pl_ytd)
- "return" → SUM(pl_ytd) / SUM(mv_base)
- "performance" == profit and loss (PL)

--------------------------------------------------
DATE / TIME  HANDLING RULES

All date columns are stored as TEXT in ISO-8601 format:
    YYYY-MM-DD

If the user mentions a date in any format,
   mentally convert it to 'YYYY-MM-DD'

------
EXAMPLES (FEW-SHOT)

User Question:
"Show number of trades per fund"

SQL:
SELECT
    portfolio_name,
    COUNT(DISTINCT trade_id) AS trade_count
FROM trade_allocation
GROUP BY portfolio_name;



--------------------------------------------------

User Question:
"Which funds performed best this year?"

SQL:
SELECT
    portfolio_name,
    SUM(pl_ytd) AS total_pl,
    SUM(mv_base) AS total_mv,
    SUM(pl_ytd) / NULLIF(SUM(mv_base), 0) AS ytd_return
FROM holding
GROUP BY portfolio_name
ORDER BY ytd_return DESC;


--------------------------------------------------

User Question:
"Top funds by YTD return as of a given date"

SQL:
SELECT
    portfolio_name,
    SUM(pl_ytd) AS total_pl,
    SUM(mv_base) AS total_mv,
    SUM(pl_ytd) / NULLIF(SUM(mv_base), 0) AS ytd_return
FROM holding
WHERE as_of_date = ?
GROUP BY portfolio_name
ORDER BY ytd_return DESC;

--------------------------------------------------

User Question:
"Total holdings per fund"

SQL:
SELECT
    portfolio_name,
    COUNT(*) AS holding_count
FROM holding
GROUP BY portfolio_name;


END OF EXAMPLES

Now generate the SQL query for the user's Query.

"""

# Gemini Text2SQL Generator (Core Function)
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set")

client = genai.Client(api_key=api_key)
MODEL_NAME = "gemini-3-flash-preview"


def generate_text2sql(user_query: str) -> dict:
    """
    Generate SQL from natural language using Gemini with manual parsing.
    Returns dict with query_bool and sql_query keys.
    """
    try:
        # Prepare the prompt
        full_prompt = f"{SYSTEM_PROMPT}\n\nUser question:\n{user_query}"
        
        # Generate content without structured output to avoid the parsing error
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=full_prompt,
        )
        
        logger.debug(f"DEBUG: Response type: {type(response)}")
        
        # Check if response exists
        if not response:
            logger.error("DEBUG: Gemini API returned None response")
            return {"query_bool": False, "sql_query": ""}
        
        # Check for blocked content via candidates
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            
            if hasattr(candidate, 'finish_reason'):
                finish_reason = str(candidate.finish_reason)
                logger.debug(f"DEBUG: Finish reason: {finish_reason}")
                
                # If content was blocked, return safe default
                if 'SAFETY' in finish_reason or 'RECITATION' in finish_reason:
                    logger.warning(f"Content blocked: {finish_reason}")
                    return {"query_bool": False, "sql_query": ""}
        
        # Extract text from response
        raw_text = None
        
        if hasattr(response, 'text') and response.text is not None:
            raw_text = response.text
            logger.debug(f"DEBUG: Using response.text")
        elif hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if (hasattr(candidate, 'content') and candidate.content and
                hasattr(candidate.content, 'parts') and candidate.content.parts):
                parts = candidate.content.parts
                if parts and hasattr(parts[0], 'text') and parts[0].text is not None:
                    raw_text = parts[0].text
                    logger.debug(f"DEBUG: Using candidate.content.parts[0].text")
        
        if raw_text is None:
            logger.error("DEBUG: Could not extract any text from response")
            return {"query_bool": False, "sql_query": ""}
        
        raw_text = raw_text.strip()
        
        # Remove markdown code blocks if present
        if raw_text.startswith("```"):
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()
        
        if not raw_text:
            logger.error("DEBUG: Empty text after cleanup")
            return {"query_bool": False, "sql_query": ""}
        
        logger.debug(f"DEBUG: Parsing text manually: {raw_text[:200]}")
        
        # Parse JSON and validate with Pydantic
        try:
            data = json.loads(raw_text)
            validated = Text2SQLResponse(**data)
            result = validated.model_dump()
            logger.debug(f"DEBUG: Successfully validated with Pydantic: {result}")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.error(f"Raw text that failed: {repr(raw_text)}")
            return {"query_bool": False, "sql_query": ""}
        except Exception as e:
            logger.error(f"Pydantic validation error: {e}")
            logger.error(f"Data that failed validation: {data}")
            return {"query_bool": False, "sql_query": ""}
        
    except Exception as e:
        logger.error(f"❌ Error generating Text2SQL: {e}")
        import traceback
        logger.error(f"DEBUG: Full traceback: {traceback.format_exc()}")
        return {"query_bool": False, "sql_query": ""}


# Example Usage
if __name__ == "__main__":
    user_question = "Which funds performed best this year?"
    
    result = generate_text2sql(user_question)
    
    print(f"\nResult: {result}")
    print(f"\nQuery bool: {result['query_bool']}")
    print(f"SQL query: {result['sql_query']}")