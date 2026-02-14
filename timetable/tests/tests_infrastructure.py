import pytest
from core.infrastructure.models import Room
from django.db import IntegrityError

@pytest.mark.django_db
class TestInfrastructureModels:

    def test_room_creation(self):
        room = Room.objects.create(
            name="LT-101",
            capacity=120,
            is_lab=False,
            location="Academic Block A"
        )
        assert str(room) == "LT-101"

    def test_room_unique_name(self):
        Room.objects.create(name="CR-01", capacity=60)
        with pytest.raises(IntegrityError):
            Room.objects.create(name="CR-01", capacity=70)