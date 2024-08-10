FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "
from transformers import pipeline;
sentiment_pipeline = pipeline('sentiment-analysis');
model = sentiment_pipeline.model;
tokenizer = sentiment_pipeline.tokenizer;
model.save_pretrained('./model');
tokenizer.save_pretrained('./model')
"

EXPOSE 5556

CMD ["python", "app.py"]
