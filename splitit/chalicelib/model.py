import uuid

from datetime import datetime

from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute, ListAttribute, NumberAttribute, MapAttribute


def _format_timestamp(timestamp):
    return datetime.strftime(timestamp, '%Y-%m-%dT%H:%M:%SZ')


def _create_id():
    return str(uuid.uuid4())


class LineItem(Model):
    class Meta:
        table_name = 'SplitItLineItems'
        region = 'us-east-2'
        host = 'http://127.0.0.1:8000'

    line_item_id = UnicodeAttribute(hash_key=True, attr_name='LineItemId', default=_create_id)
    check_id = UnicodeAttribute()
    location_id = UnicodeAttribute()
    name = UnicodeAttribute()
    amount_in_cents = NumberAttribute(default=0)
    owners = ListAttribute(default=list)

    def to_json(self):
        return {
            'lineItemId': self.line_item_id,
            'checkId': self.check_id,
            'locationId': self.location_id,
            'name': self.name,
            'amountInCents': self.amount_in_cents,
            'owners': self.owners,
        }


class Location(MapAttribute):
    location_id = UnicodeAttribute(default=_create_id)
    name = UnicodeAttribute()
    line_item_count = NumberAttribute(default=0)
    tax_in_cents = NumberAttribute(default=0)
    tip_in_cents = NumberAttribute(default=0)

    def to_json(self):
        return {
            'locationId': self.location_id,
            'name': self.name,
            'taxInCents': self.tax_in_cents,
            'tipInCents': self.tip_in_cents,
            'lineItemCount': self.line_item_count,
        }


class Check(Model):
    class Meta:
        table_name = 'SplitItChecks'
        region = 'us-east-2'
        host = 'http://127.0.0.1:8000'

    check_id = UnicodeAttribute(hash_key=True, attr_name='CheckId', default=_create_id)
    create_timestamp = UTCDateTimeAttribute(default=datetime.utcnow())
    date = UnicodeAttribute()
    description = UnicodeAttribute()
    locations = ListAttribute(of=Location, default=list)
    line_item_ids = ListAttribute(default=list)

    def to_json(self):
        check_json = {
            'checkId': self.check_id,
            'date': self.date,
            'createTimestamp': _format_timestamp(self.create_timestamp),
            'description': self.description,
        }

        check_json['locations'] = [loc.to_json() for loc in self.locations]

        return check_json
