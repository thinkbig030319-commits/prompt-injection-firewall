# Optional: containerized deployment. NOT required to run the project
# locally -- see README for the plain `uvicorn` instructions.
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python data/generate_dataset.py && python app/train.py
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
