FROM python:3.12-slim

WORKDIR /app

# Copy entire repo so both finance_service/ and mcp_servers/ are importable
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "finance_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
