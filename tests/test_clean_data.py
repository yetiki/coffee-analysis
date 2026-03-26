import pytest
from clean_data import pounds_to_kilograms, normalise_bag_weights, normalise_processing_methods, normalise_country_of_origin

def test_pounds_to_kilograms():
    assert pounds_to_kilograms(0) == 0
    assert pounds_to_kilograms(1) == 0.453592
    assert pounds_to_kilograms(10) == 4.53592

def test_normalise_bag_weights():
    assert normalise_bag_weights("60 kg") == 60
    assert normalise_bag_weights("132 lbs") == 59.874144
    assert normalise_bag_weights("100 kg") == 100
    assert normalise_bag_weights("220 lbs") == 99.79024

    with pytest.raises(ValueError):
        normalise_bag_weights("50 grams")

def test_normalise_processing_methods():
    assert normalise_processing_methods("Washed / Wet") == "Washed"
    assert normalise_processing_methods("Natural / Dry") == "Natural"
    assert normalise_processing_methods("Pulped natural / honey") == "Pulped-Natural"
    assert normalise_processing_methods("Semi-washed / Semi-pulped") == "Semi-Washed"

def test_normalise_country_of_origin():
    assert normalise_country_of_origin("Ethiopia") == "Ethiopia"
    assert normalise_country_of_origin("Cote d?Ivoire") == "Cote d'Ivoire"
