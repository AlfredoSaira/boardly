"""OpenTelemetry setup: traces, metrics, and structured logs for the board API.

Exporter choice is driven by OTEL_EXPORTER_OTLP_ENDPOINT: unset means
telemetry stays in-process (tests, local dev without the stack), set means
everything ships through the OpenTelemetry Collector.

Privacy rule: card titles and descriptions are user content and never go to
telemetry. Only routes, methods, status codes, durations, and card ids do.
"""

import json
import logging
import os
import sys

from opentelemetry import metrics, trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

RESOURCE = Resource.create(
    {
        "service.name": os.getenv("OTEL_SERVICE_NAME", "boardly-backend"),
        "deployment.environment": os.getenv("APP_ENV", "dev"),
        "service.version": os.getenv("APP_VERSION", "local"),
    }
)

OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")


class JsonFormatter(logging.Formatter):
    """One JSON object per line on stdout, carrying the active trace id."""

    def format(self, record: logging.LogRecord) -> str:
        span_context = trace.get_current_span().get_span_context()
        entry = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if span_context.is_valid:
            entry["trace_id"] = format(span_context.trace_id, "032x")
            entry["span_id"] = format(span_context.span_id, "016x")
        for key in (
            "http.route",
            "http.method",
            "http.status_code",
            "duration_ms",
            "card_id",
        ):
            if hasattr(record, key):
                entry[key] = getattr(record, key)
        return json.dumps(entry)


class StdoutHandler(logging.StreamHandler):
    """Resolve sys.stdout at write time so redirected stdout (pytest) still works."""

    @property
    def stream(self):
        return sys.stdout

    @stream.setter
    def stream(self, _value):
        pass


def setup_telemetry(app, engine):
    """Wire up tracing, metrics, and logging; return the instruments the app records."""
    tracer_provider = TracerProvider(resource=RESOURCE)
    metric_readers = []
    logger_provider = LoggerProvider(resource=RESOURCE)

    if OTLP_ENDPOINT:
        from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
            OTLPMetricExporter,
        )
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )

        tracer_provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(), schedule_delay_millis=1000)
        )
        metric_readers.append(
            PeriodicExportingMetricReader(
                OTLPMetricExporter(), export_interval_millis=5000
            )
        )
        logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(OTLPLogExporter())
        )

    trace.set_tracer_provider(tracer_provider)
    meter_provider = MeterProvider(resource=RESOURCE, metric_readers=metric_readers)
    metrics.set_meter_provider(meter_provider)

    logger = logging.getLogger("boardly")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        stdout_handler = StdoutHandler()
        stdout_handler.setFormatter(JsonFormatter())
        logger.addHandler(stdout_handler)
        logger.addHandler(
            LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
        )

    FastAPIInstrumentor.instrument_app(
        app, tracer_provider=tracer_provider, excluded_urls="healthz,readyz"
    )
    SQLAlchemyInstrumentor().instrument(engine=engine, tracer_provider=tracer_provider)

    meter = metrics.get_meter("boardly", meter_provider=meter_provider)
    requests_counter = meter.create_counter(
        "boardly_http_requests",
        description="Board API requests by route, method and HTTP status code",
    )
    duration_histogram = meter.create_histogram(
        "boardly_http_request_duration",
        unit="ms",
        description="Board API request duration by route and method",
    )
    return requests_counter, duration_histogram, logger
