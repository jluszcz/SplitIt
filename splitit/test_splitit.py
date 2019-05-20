import pytest

from chalicelib import splitit, model

ID = '88786937-E9FA-4013-9FA6-D419C3E16815'
VALID_DATE = '2019-05-20'
VALID_DESC = 'Foo bar baz'
VALID_NAME = 'Some Bar'
VALID_TAX = 100
VALID_TIP = 200


@pytest.fixture(autouse=True)
def setup_fake_ddb(mocker):
    mocker.patch('chalicelib.model.Check.save')
    mocker.patch('chalicelib.model.Check.delete')
    mocker.patch('chalicelib.model.LineItem.save')


def test_get_check_no_check(mocker):
    mocker.patch('chalicelib.model.Check.get', side_effect=model.Check.DoesNotExist)

    check = splitit.get_check(ID)

    assert check is None


def test_get_check(mocker):
    mocker.patch('chalicelib.model.Check.get', return_value=model.Check())

    check = splitit.get_check(ID)

    assert check is not None


def test_put_check_date_is_none():
    with pytest.raises(ValueError, match=r'^Invalid date'):
        splitit.put_check(date=None, description='Foo bar baz')


def test_put_check_date_is_bad():
    with pytest.raises(ValueError, match=r'^Invalid date'):
        splitit.put_check(date='20190520', description='Foo bar baz')


def test_put_check_description_is_none():
    with pytest.raises(ValueError, match=r'^Invalid description'):
        splitit.put_check(date=VALID_DATE, description=None)


def test_put_check_description_is_bad():
    with pytest.raises(ValueError, match=r'^Invalid description'):
        splitit.put_check(date=VALID_DATE, description='')


def test_put_check():
    check = splitit.put_check(date=VALID_DATE, description=VALID_DESC)

    assert check.check_id
    assert check.create_timestamp
    assert VALID_DATE == check.date
    assert VALID_DESC == check.description
    assert 1 == len(check.locations)

    loc = check.locations[0]
    assert not loc.name
    assert 0 == loc.line_item_count
    assert 0 == loc.tax_in_cents
    assert 0 == loc.tip_in_cents

    assert not check.line_item_ids


def test_update_check_no_changes():
    check = splitit.put_check(date=VALID_DATE, description=VALID_DESC)

    model.Check.save.reset_mock()

    splitit.update_check(check, date=None, description=None)

    model.Check.save.assert_not_called()


def test_update_check_invalid_date():
    check = splitit.put_check(date=VALID_DATE, description=VALID_DESC)

    with pytest.raises(ValueError, match=r'^Invalid date.*'):
        splitit.update_check(check, date='20190520', description=None)


def test_update_check_date():
    check = splitit.put_check(date=VALID_DATE, description=VALID_DESC)

    model.Check.save.reset_mock()

    new_date = '2019-05-21'
    assert VALID_DATE != new_date

    splitit.update_check(check, date=new_date, description=None)

    model.Check.save.assert_called_once()

    assert new_date == check.date
    assert VALID_DESC == check.description


def test_update_check_description():
    check = splitit.put_check(date=VALID_DATE, description=VALID_DESC)

    model.Check.save.reset_mock()

    new_desc = 'Bar baz quux'
    assert VALID_DESC != new_desc

    splitit.update_check(check, date=None, description=new_desc)

    model.Check.save.assert_called_once()

    assert VALID_DATE == check.date
    assert new_desc == check.description


def test_remove_check(mocker):
    check = splitit.put_check(date=VALID_DATE, description=VALID_DESC)
    mocker.patch('chalicelib.model.Check.get', return_value=check)

    check = splitit.remove_check(check.check_id)

    assert check is not None
    model.Check.delete.assert_called_once()


def test_remove_no_check(mocker):
    mocker.patch('chalicelib.model.Check.get', side_effect=model.Check.DoesNotExist)

    check = splitit.remove_check(ID)

    assert check is None
    model.Check.delete.assert_not_called()


def _test_put_location_invalid_tax(tax):
    check = splitit.put_check(date=VALID_DATE, description=VALID_DESC)

    with pytest.raises(ValueError, match=r'^Invalid tax'):
        splitit.put_location(check, tax_in_cents=tax)


def test_put_location_tax_is_not_int():
    _test_put_location_invalid_tax('100')


def test_put_location_tax_is_negative():
    _test_put_location_invalid_tax(-100)


def _test_put_location_invalid_tip(tip):
    check = splitit.put_check(date=VALID_DATE, description=VALID_DESC)

    with pytest.raises(ValueError, match=r'^Invalid tip'):
        splitit.put_location(check, tip_in_cents=tip)


def test_put_location_tip_is_not_int():
    _test_put_location_invalid_tip('100')


def test_put_location_tip_is_negative():
    _test_put_location_invalid_tip(-100)


def test_put_location_duplicate_name():
    check = splitit.put_check(date=VALID_DATE, description=VALID_DESC)

    with pytest.raises(ValueError, match=r'already exists'):
        splitit.put_location(check)


def test_put_location():
    check = splitit.put_check(date=VALID_DATE, description=VALID_DESC)
    location = splitit.put_location(check, location_name=VALID_NAME, tax_in_cents=VALID_TAX, tip_in_cents=VALID_TIP)

    assert 2 == len(check.locations)
    assert location in check.locations

    assert location.location_id
    assert VALID_NAME == location.name
    assert VALID_TAX == location.tax_in_cents
    assert VALID_TIP == location.tip_in_cents


def test_put_location_no_tip():
    check = splitit.put_check(date=VALID_DATE, description=VALID_DESC)
    location = splitit.put_location(check, location_name=VALID_NAME, tax_in_cents=VALID_TAX)

    assert 2 == len(check.locations)
    assert location in check.locations

    assert location.location_id
    assert VALID_NAME == location.name
    assert VALID_TAX == location.tax_in_cents
    assert not location.tip_in_cents


def test_put_location_no_tax():
    check = splitit.put_check(date=VALID_DATE, description=VALID_DESC)
    location = splitit.put_location(check, location_name=VALID_NAME, tip_in_cents=VALID_TIP)

    assert 2 == len(check.locations)
    assert location in check.locations

    assert location.location_id
    assert VALID_NAME == location.name
    assert not location.tax_in_cents
    assert VALID_TIP == location.tip_in_cents


def test_update_non_existent_location():
    check = splitit.put_check(date=VALID_DATE, description=VALID_DESC)

    model.Check.save.reset_mock()

    location = splitit.update_location(check, location_id=ID)

    assert location is None
    model.Check.save.assert_not_called()


def test_update_location():
    check = splitit.put_check(date=VALID_DATE, description=VALID_DESC)

    model.Check.save.reset_mock()

    location = check.locations[0]
    assert VALID_NAME != location.name
    assert VALID_TAX != location.tax_in_cents
    assert VALID_TIP != location.tip_in_cents

    location = splitit.update_location(check, location_id=location.location_id, name=VALID_NAME, tip_in_cents=VALID_TIP,
                                       tax_in_cents=VALID_TAX)

    assert VALID_NAME == location.name
    assert VALID_TAX == location.tax_in_cents
    assert VALID_TIP == location.tip_in_cents
    model.Check.save.assert_called_once()


def test_update_location_name():
    check = splitit.put_check(date=VALID_DATE, description=VALID_DESC)

    model.Check.save.reset_mock()

    location = check.locations[0]
    assert VALID_NAME != location.name
    assert VALID_TAX != location.tax_in_cents
    assert VALID_TIP != location.tip_in_cents

    location = splitit.update_location(check, location_id=location.location_id, name=VALID_NAME)

    assert VALID_NAME == location.name
    assert VALID_TAX != location.tax_in_cents
    assert VALID_TIP != location.tip_in_cents
    model.Check.save.assert_called_once()


def test_update_location_tip():
    check = splitit.put_check(date=VALID_DATE, description=VALID_DESC)

    model.Check.save.reset_mock()

    location = check.locations[0]
    assert VALID_NAME != location.name
    assert VALID_TAX != location.tax_in_cents
    assert VALID_TIP != location.tip_in_cents

    location = splitit.update_location(check, location_id=location.location_id, tip_in_cents=VALID_TIP)

    assert VALID_NAME != location.name
    assert VALID_TAX != location.tax_in_cents
    assert VALID_TIP == location.tip_in_cents
    model.Check.save.assert_called_once()


def test_update_location_tax():
    check = splitit.put_check(date=VALID_DATE, description=VALID_DESC)

    model.Check.save.reset_mock()

    location = check.locations[0]
    assert VALID_NAME != location.name
    assert VALID_TAX != location.tax_in_cents
    assert VALID_TIP != location.tip_in_cents

    location = splitit.update_location(check, location_id=location.location_id, tax_in_cents=VALID_TAX)

    assert VALID_NAME != location.name
    assert VALID_TAX == location.tax_in_cents
    assert VALID_TIP != location.tip_in_cents
    model.Check.save.assert_called_once()


def test_update_location_no_change():
    check = splitit.put_check(date=VALID_DATE, description=VALID_DESC)

    model.Check.save.reset_mock()

    location = check.locations[0]

    splitit.update_location(check, location_id=location.location_id)

    model.Check.save.assert_not_called()


def test_delete_only_location():
    check = splitit.put_check(date=VALID_DATE, description=VALID_DESC)

    location = check.locations[0]

    with pytest.raises(ValueError, match=r'all locations'):
        splitit.delete_location(check, location.location_id)


def test_delete_non_existent_location():
    check = splitit.put_check(date=VALID_DATE, description=VALID_DESC)

    location = splitit.delete_location(check, ID)

    assert location is None


def test_delete_location_with_line_items():
    check = splitit.put_check(date=VALID_DATE, description=VALID_DESC)

    location = check.locations[0]
    location.line_item_count += 1

    with pytest.raises(ValueError, match=r'with line items'):
        splitit.delete_location(check, location.location_id)


def test_delete_location():
    check = splitit.put_check(date=VALID_DATE, description=VALID_DESC)
    location = splitit.put_location(check, location_name=VALID_NAME)

    model.Check.save.reset_mock()

    assert 2 == len(check.locations)

    deleted = splitit.delete_location(check, location.location_id)

    assert 1 == len(check.locations)
    assert location.location_id == deleted.location_id
    model.Check.save.assert_called_once()
