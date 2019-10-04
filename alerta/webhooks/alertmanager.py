
import datetime
from typing import Any, Dict

import pytz
from dateutil.parser import parse as parse_date

from alerta.app import alarm_model
from alerta.exceptions import ApiError
from alerta.models.alert import Alert

from . import WebhookBase

JSON = Dict[str, Any]
dt = datetime.datetime


def parse_alertmanager(alert: JSON, external_url: str, related_alert=None) -> Alert:

    status = alert.get('status', 'firing')

    # Allow labels and annotations to use python string formats that refer to
    # other labels eg. runbook = 'https://internal.myorg.net/wiki/alerts/{app}/{alertname}'
    # See https://github.com/prometheus/prometheus/issues/2818

    labels = {}
    for k, v in alert['labels'].items():
        try:
            labels[k] = v.format(**alert['labels'])
        except Exception:
            labels[k] = v

    annotations = {}
    for k, v in alert['annotations'].items():
        try:
            annotations[k] = v.format(**labels)
        except Exception:
            annotations[k] = v

    starts_at = parse_date(alert['startsAt'])
    if alert['endsAt'] != '0001-01-01T00:00:00Z':
        ends_at = parse_date(alert['endsAt'])
    else:
        ends_at = None  # type: ignore

    if status == 'firing':
        severity = annotations.pop('severity', 'critical')
        create_time = starts_at
    elif status == 'resolved':
        severity = alarm_model.DEFAULT_NORMAL_SEVERITY
        create_time = ends_at
    else:
        severity = 'unknown'
        create_time = ends_at or starts_at

    # labels
    resource = labels.pop('exported_instance', None) or labels.pop('instance', 'n/a')
    event = labels.pop('event', None) or labels.pop('alertname')
    environment = labels.pop('environment', 'Production')

    customer = labels.pop('customer', None)
    correlate = labels.pop('correlate').split(',') if 'correlate' in labels else None
    service = labels.pop('service', '').split(',')
    group = labels.pop('group', None) or labels.pop('job', 'Alertmanager')
    origin = labels.pop('origin', None)
    tags = ['{}={}'.format(k, v) for k, v in labels.items()]  # any labels left over are used for tags
    tags.append(related_alert)
    try:
        timeout = int(labels.pop('timeout', 0)) or None
    except ValueError:
        timeout = None

    value = annotations.pop('value', None)
    summary = annotations.pop('summary', None)
    description = annotations.pop('description', None)

    text = description or summary or '{}: {} is {}'.format(severity.upper(), resource, event)
    if related_alert is not None:
        text = text
    if external_url:
        annotations['externalUrl'] = external_url  # needed as raw URL for bi-directional integration
    if 'generatorURL' in alert:
        annotations['moreInfo'] = '<a href="{}" target="_blank">Prometheus Graph</a>'.format(alert['generatorURL'])
    attributes = annotations  # any annotations left over are used for attributes

    return Alert(
        resource=resource,
        event=event,
        environment=environment,
        customer=customer,
        severity=severity,
        correlate=correlate,
        service=service,
        group=group,
        value=value,
        text=text,
        attributes=attributes,
        origin=origin,
        event_type='AlertmanagerAlert',
        create_time=create_time.astimezone(tz=pytz.UTC).replace(tzinfo=None),
        timeout=timeout,
        raw_data=alert,
        tags=tags
    )


class AlertmanagerWebhook(WebhookBase):
    """
    Prometheus Alertmanager webhook receiver
    See https://prometheus.io/docs/operating/integrations/#alertmanager-webhook-receiver
    """

    def incoming(self, query_string, payload):
        # tong hop event chuyen no thanh correrl
        if len(payload['alerts']>0):
            related_alert =[]
            for alert in payload['alerts']:
                related_alert.append({alert['labels']['resource']+" "+alert['labels']['event']})

        if payload and 'alerts' in payload:
            external_url = payload.get('externalURL')
            return [parse_alertmanager(alert, external_url, related_alert ) for alert in payload['alerts']]
        else:
            raise ApiError('no alerts in Prometheus notification payload', 400)
