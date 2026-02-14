import pytest
from django.db import IntegrityError
from core.times.models import Day, TimeSlot, Break


@pytest.mark.django_db
class TestTimeModels:

    def test_day_creation(self):
        day = Day.objects.create(name="Monday", is_working_day=True)
        assert str(day) == "Monday"

    def test_timeslot_unique_together(self):
        mon = Day.objects.create(name="Monday")
        TimeSlot.objects.create(day=mon, start_time="09:00", end_time="10:00", index=1)

        with pytest.raises(IntegrityError):
            TimeSlot.objects.create(day=mon, start_time="10:00", end_time="11:00", index=1)

    def test_break_creation(self):
        tue = Day.objects.create(name="Tuesday")
        br = Break.objects.create(
            day=tue,
            start_time="13:00:00",
            end_time="14:00:00"
        )
        assert "Tuesday" in str(br)