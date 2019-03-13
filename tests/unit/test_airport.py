import json
import pytest

from tests.json_loader import airport_decode

data_file = "C://Users//Xico//Documents//PycharmProjects//AllTrips//tests//fixtures//airports.json"

with open(data_file, "r", encoding="UTF-8") as source:
    airports = json.load(source, object_hook=airport_decode)


@pytest.mark.parametrize('airport', airports, ids=[airport.iata_code for airport in airports])
def test_airport_init(airport):
    assert airport.__str__() == airport.iata_code

