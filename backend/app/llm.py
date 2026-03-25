import os
import re
import json
from google import genai
from dotenv import load_dotenv
from .database import get_connection, SCHEMA_DESCRIPTION

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = f"""You are an SAP Order-to-Cash (O2C) data analyst assistant. You answer questions ONLY about the provided O2C dataset.

STRICT RULES:
1. You MUST ONLY answer questions related to the SAP Order-to-Cash dataset (sales orders, deliveries, billing documents, journal entries, payments, customers, products, plants).
2. If a user asks about anything outside this domain (general knowledge, creative writing, coding help, personal advice, etc.), respond EXACTLY with: "This system is designed to answer questions related to the SAP Order-to-Cash dataset only. Please ask a question about sales orders, deliveries, billing, payments, customers, or products."
3. Every answer MUST be backed by data from the database. Never fabricate data.
4. When you need data, generate a SQL query to retrieve it.

DATABASE SCHEMA:
{SCHEMA_DESCRIPTION}

RESPONSE FORMAT:
When the user asks a data question, respond with a JSON object in this exact format:
{{
  "type": "sql",
  "sql": "YOUR SQL QUERY HERE",
  "explanation": "Brief explanation of what this query does"
}}

When the query is off-topic, respond with:
{{
  "type": "rejection",
  "message": "This system is designed to answer questions related to the SAP Order-to-Cash dataset only. Please ask a question about sales orders, deliveries, billing, payments, customers, or products."
}}

SQL RULES:
- Use only SELECT statements. Never use INSERT, UPDATE, DELETE, DROP, ALTER, or CREATE.
- Always use LIMIT when the result set could be large (default LIMIT 50).
- Use proper JOINs based on the documented relationships.
- For the O2C flow tracing: Sales Order → Delivery (via outbound_delivery_items.referenceSdDocument) → Billing (via billing_document_items.referenceSdDocument = deliveryDocument) → Journal Entry (via journal_entry_items.referenceDocument = billingDocument) → Payment (via payments.clearingAccountingDocument = journal_entry_items.accountingDocument).
"""

ANSWER_PROMPT = """You are an SAP Order-to-Cash data analyst. Based on the SQL query results below, provide a clear, concise natural language answer.

User Question: {question}
SQL Query: {sql}
Query Results: {results}

Rules:
- Summarize the data clearly and accurately.
- Reference specific numbers, document IDs, or names from the results.
- If results are empty, say so clearly.
- Keep the answer focused and professional.
- Format numbers and lists for readability.
- Do NOT include the SQL query in your response. Only provide the natural language answer.
"""

def is_safe_sql(sql: str) -> bool:
    sql_upper = sql.upper().strip()
    dangerous = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "EXEC", "EXECUTE", "--", ";--"]
    for keyword in dangerous:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, sql_upper):
            if keyword in ("CREATE", "DROP", "ALTER"):
                return False
            if keyword in ("INSERT", "UPDATE", "DELETE", "TRUNCATE"):
                return False
    if sql_upper.count(";") > 1:
        return False
    return sql_upper.startswith("SELECT")

def extract_json_from_response(text: str) -> dict:
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    return None

def query_llm(user_question: str, conversation_history: list = None) -> dict:
    messages = []
    if conversation_history:
        for msg in conversation_history[-6:]:
            role = "model" if msg["role"] == "assistant" else "user"
            messages.append({"role": role, "parts": [{"text": msg["content"]}]})

    messages.append({"role": "user", "parts": [{"text": user_question}]})

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=messages,
            config={
                "system_instruction": SYSTEM_PROMPT,
                "temperature": 0.1,
                "max_output_tokens": 2048,
            }
        )

        response_text = response.text
        parsed = extract_json_from_response(response_text)

        if not parsed:
            if any(kw in user_question.lower() for kw in [
                "weather", "recipe", "joke", "poem", "story", "write me", "hello",
                "who are you", "what are you", "how are you", "capital of",
                "president", "explain me", "teach me", "code", "programming"
            ]):
                return {
                    "type": "rejection",
                    "answer": "This system is designed to answer questions related to the SAP Order-to-Cash dataset only. Please ask a question about sales orders, deliveries, billing, payments, customers, or products."
                }
            return {"type": "text", "answer": response_text}

        if parsed.get("type") == "rejection":
            return {"type": "rejection", "answer": parsed.get("message", "This system is designed to answer questions related to the SAP Order-to-Cash dataset only.")}

        if parsed.get("type") == "sql" and parsed.get("sql"):
            sql = parsed["sql"].strip().rstrip(";")

            if not is_safe_sql(sql):
                return {"type": "error", "answer": "The generated query was rejected for safety reasons. Only SELECT queries are allowed."}

            conn = get_connection()
            cur = conn.cursor()
            try:
                cur.execute(sql)
                rows = cur.fetchall()
                results = [dict(r) for r in rows]
            except Exception as e:
                conn.close()
                return {"type": "error", "answer": f"SQL execution error: {str(e)}", "sql": sql}
            finally:
                conn.close()

            results_str = json.dumps(results[:100], default=str)

            if not results:
                return {
                    "type": "sql",
                    "answer": "The query returned no results. Try rephrasing your question or checking if the referenced entities exist in the dataset.",
                    "sql": sql,
                    "rowCount": 0,
                    "data": [],
                }

            answer_response = client.models.generate_content(
                model=MODEL,
                contents=[{"role": "user", "parts": [{"text": ANSWER_PROMPT.format(question=user_question, sql=sql, results=results_str)}]}],
                config={"temperature": 0.2, "max_output_tokens": 2048}
            )

            return {
                "type": "sql",
                "answer": answer_response.text,
                "sql": sql,
                "rowCount": len(results),
                "data": results[:50],
            }

        return {"type": "text", "answer": response_text}

    except Exception as e:
        return {"type": "error", "answer": f"An error occurred: {str(e)}"}
