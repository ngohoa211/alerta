import datetime
from typing import Any, Dict
import logging
import pytz
from dateutil.parser import parse as parse_date

from alerta.app import alarm_model
from alerta.exceptions import ApiError
from alerta.models.alert import Alert

from . import WebhookBase

JSON = Dict[str, Any]
dt = datetime.datetime

LOG = logging.getLogger('alerta.webhook')


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
    #service = labels.pop('service', '')
    group = labels.pop('group', None) or labels.pop('job', 'Alertmanager')
    origin = labels.pop('origin', None)
    tags = ['{}={}'.format(k, v) for k, v in labels.items()]  # any labels left over are used for tags
    #tags.append(related_alert)
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
    if 'moreInfo' in alert:
        annotations['moreInfo'] = alert['moreInfo']
    #attributes = annotations  # any annotations left over are used for attributes
    attributes = {"related_alert":related_alert}

    # logging.error(resource)
    # logging.error(event)
    # logging.error(environment)
    # logging.error(customer)
    # logging.error(correlate)
    # logging.error(service)
    # logging.error(group)
    # logging.error(value)
    # logging.error(text)
    # logging.error(attributes)
    # logging.error(origin)
    # logging.error(timeout)
    # logging.error(tags)
    #logging.error(tags)
    new_alert = Alert(
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
        #create_time=create_time.astimezone(tz=pytz.UTC).replace(tzinfo=None),
        timeout=timeout,
        raw_data=alert,
        tags=tags
    )
    #logging.error(new_alert)
    return new_alert


# INPUT: {"receiver":"anht","status":"firing","alerts":[{"status":"firing","labels":{"environment":"Production","event":"no_metric_system-host=compute01","group":"OS","instance":"{\"host\": \"compute01\"}","origin":"VNA","service":"deadman_check"},"annotations":{"severity":"critical","summary":"lose metric system","value":"['time', 'emitted']:[['2019-10-07T11:26:00Z', 0]]"},"startsAt":"2019-10-07T11:26:00.571099875Z","endsAt":"0001-01-01T00:00:00Z","generatorURL":"","fingerprint":"b939eb01b8bbb940"},{"status":"firing","labels":{"environment":"Production","event":"no_metric_system-host=compute02","group":"OS","instance":"{\"host\": \"compute02\"}","origin":"VNA","service":"deadman_check"},"annotations":{"severity":"critical","summary":"lose metric system","value":"['time', 'emitted']:[['2019-10-07T11:26:00Z', 0]]"},"startsAt":"2019-10-07T11:26:00.255422902Z","endsAt":"0001-01-01T00:00:00Z","generatorURL":"","fingerprint":"988537c811e071e0"},{"status":"firing","labels":{"environment":"Production","event":"no_metric_system-host=controller","group":"OS","instance":"{\"host\": \"controller\"}","origin":"VNA","service":"deadman_check"},"annotations":{"severity":"critical","summary":"lose metric system","value":"['time', 'emitted']:[['2019-10-07T11:26:00Z', 0]]"},"startsAt":"2019-10-07T11:26:00.869522957Z","endsAt":"0001-01-01T00:00:00Z","generatorURL":"","fingerprint":"c2c7c41655f0160a"}],"groupLabels":{"group":"OS","origin":"VNA","service":"deadman_check"},"commonLabels":{"environment":"Production","group":"OS","origin":"VNA","service":"deadman_check"},"commonAnnotations":{"severity":"critical","summary":"lose metric system","value":"['time', 'emitted']:[['2019-10-07T11:26:00Z', 0]]"},"externalURL":"http://monitor:9093","version":"4","groupKey":"{}/{}:{group=\"OS\", origin=\"VNA\", service=\"deadman_check\"}"}
#
class AlertmanagerWebhook(WebhookBase):
    """
    Prometheus Alertmanager webhook receiver
    See https://prometheus.io/docs/operating/integrations/#alertmanager-webhook-receiver
    """

    def incoming(self, query_string, payload):
        # logging.info("get alert: %s", payload['alerts'])
        # transform this alert group to related each other
        related_alert = []
        for alert in payload['alerts']:
            related_alert.append(alert['labels']['event'])

        #logging.info(related_alert)
        if payload and 'alerts' in payload:
            external_url = payload.get('externalURL')
            try:
                return [parse_alertmanager(alert, external_url, related_alert) for alert in payload['alerts']]
            except Exception as e:
                logging.error(e)
                raise ApiError('Error : '+e, 400)
        else:
            raise ApiError('no alerts in Alertmanager notification payload', 400)


