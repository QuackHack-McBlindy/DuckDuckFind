FROM python:3.11-slim

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5556


WORKDIR /app


COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5556

CMD ["flask", "run"]
