import os
import tempfile
import numpy
from matchms import Spectrum
from matchms.exporting import save_as_json
from matchms.importing import load_from_json


def test_save_and_load_json_single_spectrum():
    """Test saving spectrum to .json file"""
    spectrum = Spectrum(mz=numpy.array([100, 200, 300], dtype="float"),
                        intensities=numpy.array([10, 10, 500], dtype="float"),
                        metadata={"charge": -1,
                                  "inchi": '"InChI=1S/C6H12"',
                                  "precursor_mz": 222.2,
                                  "test_field": "test"})
    # Write to test file
    with tempfile.TemporaryDirectory() as d:
        filename = os.path.join(d, "test.json")
        save_as_json(spectrum, filename)

        # test if file exists
        assert os.path.isfile(filename)

        # Test if content of json file is correct
        spectrum_import = load_from_json(filename)[0]
        assert spectrum_import == spectrum, "Original and saved+loaded spectrum not identical"


def test_save_and_load_json_spectrum_list():
    """Test saving spectrum list to .json file"""
    spectrum1 = Spectrum(mz=numpy.array([100, 200, 300], dtype="float"),
                         intensities=numpy.array([10, 10, 500], dtype="float"),
                         metadata={"test_field": "test1"})

    spectrum2 = Spectrum(mz=numpy.array([100, 200, 300], dtype="float"),
                         intensities=numpy.array([10, 10, 500], dtype="float"),
                         metadata={"test_field": "test2"})
    # Write to test file
    with tempfile.TemporaryDirectory() as d:
        filename = os.path.join(d, "test.json")
        save_as_json([spectrum1, spectrum2], filename)

        # test if file exists
        assert os.path.isfile(filename)

        # Test if content of json file is correct
        spectrum_imports = load_from_json(filename)
        assert spectrum_imports[0] == spectrum1, "Original and saved+loaded spectrum not identical"
        assert spectrum_imports[1] == spectrum2, "Original and saved+loaded spectrum not identical"

def test_load_from_json_zero_peaks(tmp_path):
    spectrum1 = Spectrum(mz=numpy.array([], dtype="float"),
                         intensities=numpy.array([], dtype="float"),
                         metadata={"test_field": "test1"})

    filename = tmp_path / "test.json"

    save_as_json([spectrum1], filename)

    # test if file exists
    assert os.path.isfile(filename)

    # Test if content of json file is correct
    spectrum_imports = load_from_json(filename)
    assert len(spectrum_imports) == 0, "Spectrum without peaks should be skipped"                
