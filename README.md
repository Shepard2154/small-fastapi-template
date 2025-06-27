# small-fastapi-template

## Команда для запуска
OTEL_SERVICE_NAME=service.name=small-fastapi-template OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true \
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 OTEL_EXPORTER_OTLP_INSECURE=true \
opentelemetry-instrument python main.py