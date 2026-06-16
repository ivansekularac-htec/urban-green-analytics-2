from unittest.mock import Mock

from app.crud.farms import farm as farm_crud
from app.models.farms.farm import Farm
from app.models.farms.farm_status import FarmStatus
from app.schemas.farms.farm import FarmCreate, FarmUpdate


def test_create_farm():
    db = Mock()

    payload = FarmCreate(
        infrastructure_type_id=1,
        growing_system_type_id=1,
        name="Test Farm",
        status=FarmStatus.ACTIVE,
    )

    result = farm_crud.create(
        db=db,
        payload=payload,
    )

    assert isinstance(result, Farm)
    assert result.name == "Test Farm"

    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once()


def test_get_farm():
    db = Mock()

    farm = Farm(
        id=1,
        infrastructure_type_id=1,
        growing_system_type_id=1,
        name="Farm",
        status=FarmStatus.ACTIVE,
    )

    db.get.return_value = farm

    result = farm_crud.get(
        db=db,
        farm_id=1,
    )

    assert result == farm

    db.get.assert_called_once_with(
        Farm,
        1,
    )


def test_get_farm_not_found():
    db = Mock()

    db.get.return_value = None

    result = farm_crud.get(
        db=db,
        farm_id=999,
    )

    assert result is None


def test_get_all_farms():
    db = Mock()

    farms = [
        Farm(
            id=1,
            infrastructure_type_id=1,
            growing_system_type_id=1,
            name="Farm 1",
            status=FarmStatus.ACTIVE,
        ),
        Farm(
            id=2,
            infrastructure_type_id=1,
            growing_system_type_id=1,
            name="Farm 2",
            status=FarmStatus.ACTIVE,
        ),
    ]

    db.scalars.return_value.all.return_value = farms

    result = farm_crud.get_all(db)

    assert len(result) == 2


def test_update_farm():
    db = Mock()

    farm = Farm(
        id=1,
        infrastructure_type_id=1,
        growing_system_type_id=1,
        name="Old Name",
        status=FarmStatus.ACTIVE,
    )

    payload = FarmUpdate(
        name="New Name",
    )

    result = farm_crud.update(
        db=db,
        farm=farm,
        payload=payload,
    )

    assert result.name == "New Name"

    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(farm)


def test_delete_farm():
    db = Mock()

    farm = Farm(
        id=1,
        infrastructure_type_id=1,
        growing_system_type_id=1,
        name="Farm",
        status=FarmStatus.ACTIVE,
    )

    farm_crud.delete(
        db=db,
        farm=farm,
    )

    db.delete.assert_called_once_with(farm)
    db.commit.assert_called_once()
