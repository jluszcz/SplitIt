import pytest

from chalicelib import splitit, model

ID = '88786937-E9FA-4013-9FA6-D419C3E16815'
VALID_DATE = '2019-05-20'
VALID_DESC = 'Foo bar baz'


@pytest.fixture(autouse=True)
def setup_fake_ddb(mocker):
    mocker.patch('chalicelib.model.Check.save')
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
    with pytest.raises(ValueError, match=r'^Invalid date.*'):
        splitit.put_check(date=None, description='Foo bar baz')


def test_put_check_date_is_bad():
    with pytest.raises(ValueError, match=r'^Invalid date.*'):
        splitit.put_check(date='20190520', description='Foo bar baz')


def test_put_check_description_is_none():
    with pytest.raises(ValueError, match=r'^Invalid description.*'):
        splitit.put_check(date=VALID_DATE, description=None)


def test_put_check_description_is_bad():
    with pytest.raises(ValueError, match=r'^Invalid description.*'):
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
