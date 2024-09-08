FROM python:3.11-slim

ENV FLASK_APP=app/main.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5556
ENV FLASK_ENV=development
ENV FLASK_DEBUG=1 

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/app/Media/Photos && \
    chown -R www-data:www-data /app/app/Media/Photos

USER www-data

EXPOSE 5556

CMD ["flask", "run", "--host=0.0.0.0", "--port=5556"]
