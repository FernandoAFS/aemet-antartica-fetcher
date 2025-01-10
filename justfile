set dotenv-load

export OTEL_PYTHON_LOG_CORRELATION := "true"
export OTEL_PYTHON_LOG_FORMAT :="%(msg)s [span_id=%(span_id)s]"
export OTEL_PYTHON_LOG_LEVEL := "debug"
export OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED := "true"

dev-run:
    poetry run \
    fastapi dev aemetAntartica/app/app.py

otel-run:
    poetry run \
    opentelemetry-instrument \
        --exporter_otlp_insecure true \
        --traces_exporter console,otlp \
        --metrics_exporter console,otlp \
        --logs_exporter console,otlp \
        --service_name aemet-antartica \
        --exporter_otlp_endpoint 127.0.0.1:4317 \
        fastapi run aemetAntartica/app/app.py
