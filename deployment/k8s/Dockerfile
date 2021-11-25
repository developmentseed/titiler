ARG PYTHON_VERSION=3.9

FROM python:${PYTHON_VERSION}-slim

RUN pip install --no-cache-dir --upgrade titiler.application["server"]

CMD ["uvicorn", "titiler.application.main:app", "--host", "0.0.0.0", "--port", "80"]
