#!/usr/bin/env python

import argparse
import json
import requests

ENDPOINT = 'http://127.0.0.1:9000'


def add_check(args):
    data = {
        'date': args.date,
        'description': args.description,
    }

    return requests.post('%s/check' % (ENDPOINT), json=data)


def get_check(args):
    return requests.get('%s/check/%s' % (ENDPOINT, args.check_id))


def update_check(args):
    data = {}

    if args.date:
        data['date'] = args.date

    if args.description:
        data['description'] = args.description

    return requests.put('%s/check/%s' % (ENDPOINT, args.check_id), json=data)


def remove_check(args):
    return requests.delete('%s/check/%s' % (ENDPOINT, args.check_id))


def add_location(args):
    data = {
        'name': args.name,
    }

    if args.tax_in_cents is not None:
        data['taxInCents'] = args.tax_in_cents

    if args.tip_in_cents is not None:
        data['tipInCents'] = args.tip_in_cents

    return requests.post('%s/check/%s/location' % (ENDPOINT, args.check_id), json=data)


def update_location(args):
    data = {}

    if args.name:
        data['name'] = args.name

    if args.tax_in_cents is not None:
        data['taxInCents'] = args.tax_in_cents

    if args.tip_in_cents is not None:
        data['tipInCents'] = args.tip_in_cents

    return requests.put('%s/check/%s/location/%s' % (ENDPOINT, args.check_id, args.location_id), json=data)


def remove_location(args):
    return requests.delete('%s/check/%s/location/%s' % (ENDPOINT, args.check_id, args.location_id))


def add_line_item(args):
    data = {
        'description': args.description,
    }

    if args.owners:
        data['owners'] = args.owners

    if args.location_id:
        data['locationId'] = args.location_id

    if args.amount_in_cents is not None:
        data['amountInCents'] = args.amount_in_cents

    return requests.post('%s/check/%s/line-item' % (ENDPOINT, args.check_id), json=data)


def parse_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    add_check_subparser = subparsers.add_parser('add-check')
    add_check_subparser.add_argument('--date', required=True)
    add_check_subparser.add_argument('--description', required=True)
    add_check_subparser.set_defaults(func=add_check)

    get_check_subparser = subparsers.add_parser('get-check')
    get_check_subparser.add_argument('--check-id', required=True)
    get_check_subparser.set_defaults(func=get_check)

    update_check_subparser = subparsers.add_parser('update-check')
    update_check_subparser.add_argument('--check-id', required=True)
    update_check_subparser.add_argument('--date')
    update_check_subparser.add_argument('--description')
    update_check_subparser.set_defaults(func=update_check)

    remove_check_subparser = subparsers.add_parser('remove-check')
    remove_check_subparser.add_argument('--check-id', required=True)
    remove_check_subparser.set_defaults(func=remove_check)

    add_location_subparser = subparsers.add_parser('add-location')
    add_location_subparser.add_argument('--check-id', required=True)
    add_location_subparser.add_argument('--name', required=True)
    add_location_subparser.add_argument('--tax-in-cents', type=int)
    add_location_subparser.add_argument('--tip-in-cents', type=int)
    add_location_subparser.set_defaults(func=add_location)

    update_location_subparser = subparsers.add_parser('update-location')
    update_location_subparser.add_argument('--check-id', required=True)
    update_location_subparser.add_argument('--location-id', required=True)
    update_location_subparser.add_argument('--name')
    update_location_subparser.add_argument('--tax-in-cents', type=int)
    update_location_subparser.add_argument('--tip-in-cents', type=int)
    update_location_subparser.set_defaults(func=update_location)

    remove_location_subparser = subparsers.add_parser('remove-location')
    remove_location_subparser.add_argument('--check-id', required=True)
    remove_location_subparser.add_argument('--location-id', required=True)
    remove_location_subparser.set_defaults(func=remove_location)

    add_line_item_subparser = subparsers.add_parser('add-line-item')
    add_line_item_subparser.add_argument('--check-id', required=True)
    add_line_item_subparser.add_argument('--description', required=True)
    add_line_item_subparser.add_argument('--location-id')
    add_line_item_subparser.add_argument('--owners', nargs='+')
    add_line_item_subparser.add_argument('--amount-in-cents', type=int)
    add_line_item_subparser.set_defaults(func=add_line_item)

    return parser.parse_args()


def main():
    args = parse_args()

    response = args.func(args)

    print(json.dumps(response.json(), indent=4))


if __name__ == '__main__':
    main()
