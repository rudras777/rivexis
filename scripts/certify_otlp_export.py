#!/usr/bin/env python3
"""Local OTLP/HTTP protobuf certification for Rivexis.

Starts a loopback collector stub, enables Rivexis OTLP synchronously, emits a server
span plus child provider/error spans, parses the received protobuf payloads, and
verifies trace/parent linkage plus P35 exception-confidentiality behavior. No external
network is required.
"""
from __future__ import annotations

import gzip
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'apps'/'api'))

from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest  # noqa:E402
from rivexis_api.core.telemetry import child_span, init_telemetry, request_span, shutdown_telemetry, telemetry_export_status  # noqa:E402

received=[]

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length=int(self.headers.get('Content-Length','0'))
        body=self.rfile.read(length)
        if self.headers.get('Content-Encoding','').lower()=='gzip':
            body=gzip.decompress(body)
        req=ExportTraceServiceRequest()
        try:req.ParseFromString(body)
        except Exception:
            self.send_response(400);self.end_headers();return
        received.append((self.path,self.headers.get('Content-Type',''),req))
        self.send_response(200);self.send_header('Content-Type','application/x-protobuf');self.end_headers();self.wfile.write(b'')
    def log_message(self,*args):return

def spans_from(req):
    for resource_spans in req.resource_spans:
        for scope_spans in resource_spans.scope_spans:
            for span in scope_spans.spans:
                yield span

def main()->int:
    server=HTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    endpoint=f'http://127.0.0.1:{server.server_port}/v1/traces'
    old={k:os.environ.get(k) for k in ['RIVEXIS_OTEL_ENABLED','RIVEXIS_OTEL_SYNC_EXPORT','OTEL_EXPORTER_OTLP_TRACES_ENDPOINT','OTEL_SERVICE_NAME','RIVEXIS_RELEASE_VERSION']}
    try:
        os.environ['RIVEXIS_OTEL_ENABLED']='true'
        os.environ['RIVEXIS_OTEL_SYNC_EXPORT']='true'
        os.environ['OTEL_EXPORTER_OTLP_TRACES_ENDPOINT']=endpoint
        os.environ['OTEL_SERVICE_NAME']='rivexis-certification'
        os.environ['RIVEXIS_RELEASE_VERSION']='2.2.0'
        shutdown_telemetry();init_telemetry(force=True)
        incoming_trace='1234567890abcdef1234567890abcdef';parent='abcdef1234567890'
        secret_sentinel='P35-SECRET-MUST-NOT-ENTER-OTLP'
        with request_span('GET /certification',incoming_traceparent=f'00-{incoming_trace}-{parent}-01',attributes={'certification':'otlp'}) as root:
            with child_span('provider.certification.get',kind='client',attributes={'rivexis.provider.id':'certification'}) as child:
                child_id=child.context.span_id
            try:
                with child_span('provider.certification.error',kind='client',attributes={'rivexis.provider.id':'certification'}):
                    raise RuntimeError(secret_sentinel)
            except RuntimeError:
                pass
            root_id=root.context.span_id
            trace_id=root.context.trace_id
        shutdown_telemetry()
        all_spans=[span for _,_,req in received for span in spans_from(req)]
        by_name={span.name:span for span in all_spans}
        if trace_id!=incoming_trace:raise AssertionError('incoming W3C trace id was not preserved')
        required={'GET /certification','provider.certification.get','provider.certification.error'}
        if not required.issubset(by_name):raise AssertionError(f'missing spans: {sorted(required-set(by_name))}')
        root_span=by_name['GET /certification'];child_span_pb=by_name['provider.certification.get'];error_span=by_name['provider.certification.error']
        if root_span.trace_id.hex()!=incoming_trace:raise AssertionError('root exported trace id mismatch')
        if root_span.span_id.hex()!=root_id:raise AssertionError('root exported span id mismatch')
        if root_span.parent_span_id.hex()!=parent:raise AssertionError('remote parent span id mismatch')
        if child_span_pb.trace_id.hex()!=incoming_trace:raise AssertionError('child trace id mismatch')
        if child_span_pb.span_id.hex()!=child_id:raise AssertionError('child span id mismatch')
        if child_span_pb.parent_span_id.hex()!=root_id:raise AssertionError('child parent linkage mismatch')
        # P35 confidentiality: exception payloads/stack traces are not exported.
        if error_span.events:
            raise AssertionError('error span exported exception events/stacktrace')
        attrs={kv.key:kv.value.string_value for kv in error_span.attributes if kv.value.WhichOneof('value')=='string_value'}
        if attrs.get('exception.type')!='RuntimeError':
            raise AssertionError(f'exception type missing from sanitized error span: {attrs}')
        if secret_sentinel in str(error_span):
            raise AssertionError('secret exception message entered OTLP protobuf')
        if error_span.status.message:
            raise AssertionError('error span status description must be empty')
        paths={path for path,_,_ in received};types={ctype for _,ctype,_ in received}
        if paths!={'/v1/traces'}:raise AssertionError(f'unexpected OTLP paths: {paths}')
        if not all('application/x-protobuf' in ctype for ctype in types):raise AssertionError(f'unexpected content types: {types}')
        status=telemetry_export_status()
        if status['attempts']<2 or status['successes']<2 or status['failures']!=0:raise AssertionError(f'bad export status: {status}')
        print(f"OTLP certification: PASS ({len(all_spans)} spans; W3C parent linkage; protobuf HTTP; exception payload redaction; endpoint /v1/traces)")
        return 0
    except Exception as exc:
        print(f'OTLP certification: FAIL - {exc}',file=sys.stderr);return 1
    finally:
        try:shutdown_telemetry()
        except Exception:pass
        server.shutdown();server.server_close();thread.join(timeout=2)
        for key,val in old.items():
            if val is None:os.environ.pop(key,None)
            else:os.environ[key]=val

if __name__=='__main__':raise SystemExit(main())
