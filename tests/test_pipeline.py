import os
import numpy as np
import pytest
from matchms import Pipeline
from matchms.filtering import select_by_mz
from matchms.Pipeline import create_workflow
from matchms.similarity import ModifiedCosine
from matchms.yaml_file_functions import load_workflow_from_yaml_file


module_root = os.path.join(os.path.dirname(__file__), "..")
spectrums_file_msp = os.path.join(module_root, "tests", "testdata", "massbank_five_spectra.msp")


def test_pipeline_initial_check_missing_file():
    workflow = create_workflow(score_computations=[["precursormzmatch",  {"tolerance": 120.0}]])
    pipeline = Pipeline(workflow)
    with pytest.raises(AssertionError) as msg:
        pipeline.run("non_existing_file.msp")
    assert "not exist" in str(msg.value)


def test_pipeline_initial_check_unknown_step():
    workflow = create_workflow(score_computations=[["precursormzOOPSmatch",  {"tolerance": 120.0}]])
    with pytest.raises(ValueError) as msg:
        Pipeline(workflow)
    assert "Unknown score computation:" in str(msg.value)


def test_pipeline_symmetric():
    workflow = create_workflow(predefined_processing_queries="basic",
        score_computations=[["precursormzmatch",  {"tolerance": 120.0}],
                                                   ["modifiedcosine", {"tolerance": 10.0}]])
    pipeline = Pipeline(workflow)
    pipeline.run(spectrums_file_msp)

    assert len(pipeline.spectrums_queries) == 5
    assert pipeline.spectrums_queries[0] == pipeline.spectrums_references[0]
    assert pipeline.is_symmetric is True
    assert pipeline.scores.scores.shape == (5, 5, 3)
    assert pipeline.scores.score_names == ('PrecursorMzMatch', 'ModifiedCosine_score', 'ModifiedCosine_matches')
    all_scores = pipeline.scores.to_array()
    expected = np.array([[1., 0.30384404],
                         [0.30384404, 1.]])
    assert np.allclose(all_scores["ModifiedCosine_score"][3:, 3:], expected)
    assert np.allclose(all_scores["ModifiedCosine_score"].diagonal(), 1), "Diagonal should all be 1.0"


def test_pipeline_symmetric_filters():
    workflow = create_workflow(predefined_processing_queries="basic",
                               additional_filters_queries=[[select_by_mz, {"mz_from": 0, "mz_to": 1000}]],
                               score_computations=[["precursormzmatch",  {"tolerance": 120.0}],
                                                   ["modifiedcosine", {"tolerance": 10.0}]])
    pipeline = Pipeline(workflow)
    pipeline.run(spectrums_file_msp)

    assert len(pipeline.spectrums_queries) == 5
    assert pipeline.spectrums_queries[0].metadata == pipeline.spectrums_references[0].metadata
    assert pipeline.spectrums_queries[0] == pipeline.spectrums_references[0]
    assert pipeline.is_symmetric is True
    assert pipeline.scores.scores.shape == (5, 5, 3)
    assert pipeline.scores.score_names == ('PrecursorMzMatch', 'ModifiedCosine_score', 'ModifiedCosine_matches')
    all_scores = pipeline.scores.to_array()
    expected = np.array([[1., 0.30384404],
                         [0.30384404, 1.]])
    assert np.allclose(all_scores["ModifiedCosine_score"][3:, 3:], expected)
    assert np.allclose(all_scores["ModifiedCosine_score"].diagonal(), 1), "Diagonal should all be 1.0"


def test_pipeline_symmetric_masking():
    workflow = create_workflow(predefined_processing_queries="basic",
                               score_computations=[["precursormzmatch",  {"tolerance": 120.0}],
                                   ["modifiedcosine", {"tolerance": 10.0}],
                                   ["filter_by_range", {"low": 0.3, "above_operator": '>='}]])
    pipeline = Pipeline(workflow)
    pipeline.run(spectrums_file_msp)

    assert len(pipeline.spectrums_queries) == 5
    assert pipeline.spectrums_queries[0] == pipeline.spectrums_references[0]
    assert pipeline.is_symmetric is True
    assert pipeline.scores.scores.shape == (5, 5, 3)
    assert pipeline.scores.score_names == ('PrecursorMzMatch', 'ModifiedCosine_score', 'ModifiedCosine_matches')
    all_scores = pipeline.scores.to_array()
    expected = np.array([[1., 0.30384404],
                         [0.30384404, 1.]])
    assert np.allclose(all_scores["ModifiedCosine_score"][3:, 3:], expected)
    assert np.allclose(all_scores["ModifiedCosine_score"].diagonal(), 1), "Diagonal should all be 1.0"


def test_pipeline_symmetric_custom_score():
    workflow = create_workflow(predefined_processing_queries="basic",
                               score_computations=[["precursormzmatch",  {"tolerance": 120.0}],
                                                   [ModifiedCosine, {"tolerance": 10.0}]])
    pipeline = Pipeline(workflow)
    pipeline.run(spectrums_file_msp)

    assert len(pipeline.spectrums_queries) == 5
    assert pipeline.spectrums_queries[0] == pipeline.spectrums_references[0]
    assert pipeline.is_symmetric is True
    assert pipeline.scores.scores.shape == (5, 5, 3)
    assert pipeline.scores.score_names == ('PrecursorMzMatch', 'ModifiedCosine_score', 'ModifiedCosine_matches')
    all_scores = pipeline.scores.to_array()
    expected = np.array([[1., 0.30384404],
                         [0.30384404, 1.]])
    assert np.allclose(all_scores["ModifiedCosine_score"][3:, 3:], expected)
    assert np.allclose(all_scores["ModifiedCosine_score"].diagonal(), 1), "Diagonal should all be 1.0"


def test_pipeline_non_symmetric():
    """Test importing from multiple files and different inputs for query and references."""
    workflow = create_workflow(predefined_processing_queries="basic",
                               predefined_processing_reference="basic",
                               score_computations=[["precursormzmatch",  {"tolerance": 120.0}],
                                                   ["modifiedcosine", {"tolerance": 10.0}]])
    pipeline = Pipeline(workflow)
    pipeline.run(spectrums_file_msp, [spectrums_file_msp, spectrums_file_msp])

    assert len(pipeline.spectrums_queries) == 5
    assert len(pipeline.spectrums_references) == 10
    assert pipeline.spectrums_queries[0] == pipeline.spectrums_references[5]
    assert pipeline.is_symmetric is False
    assert pipeline.scores.scores.shape == (10, 5, 3)
    assert pipeline.scores.score_names == ('PrecursorMzMatch', 'ModifiedCosine_score', 'ModifiedCosine_matches')
    all_scores = pipeline.scores.to_array()
    assert np.all(all_scores[:5, :] == all_scores[5:, :])
    expected = np.array([[1., 0.30384404],
                         [0.30384404, 1.]])
    assert np.allclose(all_scores["ModifiedCosine_score"][8:, 3:], expected)


def test_pipeline_from_yaml():
    pytest.importorskip("rdkit")
    config_file = os.path.join(module_root, "tests", "test_pipeline.yaml")
    workflow = load_workflow_from_yaml_file(config_file)
    pipeline = Pipeline(workflow)
    pipeline.run(spectrums_file_msp)
    assert len(pipeline.spectrums_queries) == 5
    assert pipeline.spectrums_queries[0] == pipeline.spectrums_references[0]
    assert pipeline.is_symmetric is True
    assert pipeline.scores.scores.shape == (5, 5, 3)
    assert pipeline.scores.score_names == ('PrecursorMzMatch', 'ModifiedCosine_score', 'ModifiedCosine_matches')
    all_scores = pipeline.scores.to_array()
    expected = np.array([[1., 0.30384404],
                         [0.30384404, 1.]])
    assert np.allclose(all_scores["ModifiedCosine_score"][3:, 3:], expected)


def test_pipeline_to_and_from_yaml(tmp_path):
    pytest.importorskip("rdkit")
    config_file = os.path.join(tmp_path, "test_pipeline.yaml")

    workflow = create_workflow(config_file, score_computations=[["precursormzmatch",  {"tolerance": 120.0}],
                                                                ["modifiedcosine", {"tolerance": 10.0}]])
    assert os.path.exists(config_file)

    pipeline = Pipeline(workflow)
    pipeline.run(spectrums_file_msp)
    scores_run1 = pipeline.scores

    # Load again
    workflow = load_workflow_from_yaml_file(config_file)
    pipeline = Pipeline(workflow)
    pipeline.run(spectrums_file_msp)
    assert pipeline.scores.scores == scores_run1.scores


def test_pipeline_logging(tmp_path):
    pytest.importorskip("rdkit")
    workflow = create_workflow()
    pipeline = Pipeline(workflow)
    logfile = os.path.join(tmp_path, "testlog.log")
    pipeline.logging_file = logfile
    pipeline.run(spectrums_file_msp)

    assert os.path.exists(logfile)
    with open(logfile, "r", encoding="utf-8") as f:
        firstline = f.readline().rstrip()
    assert "Start running matchms pipeline" in firstline


def test_FingerprintSimilarity_pipeline():
    pytest.importorskip("rdkit")
    workflow = create_workflow(predefined_processing_queries="basic",
                               additional_filters_queries=["add_fingerprint"],
                               predefined_processing_reference="basic",
                               additional_filters_references=["add_fingerprint"],
                               score_computations=[["metadatamatch", {"field": "precursor_mz", "matching_type": "difference", "tolerance": 50}],
                                                   ["fingerprintsimilarity", {"similarity_measure": "jaccard"}]],
                               )
    pipeline = Pipeline(workflow)
    pipeline.run(spectrums_file_msp, spectrums_file_msp)
    assert len(pipeline.spectrums_queries[0].get("fingerprint")) == 2048
    assert pipeline.scores.scores.shape == (5, 5, 2)
    assert pipeline.scores.score_names == ('MetadataMatch', 'FingerprintSimilarity')


def test_pipeline_changing_workflow():
    """Test if changing workflow after creating Pipeline results in the expected change of the pipeline"""
    workflow = create_workflow(predefined_processing_queries=None,
                               additional_filters_queries=["make_charge_int"],
                               predefined_processing_reference=None,
                               additional_filters_references=["make_charge_int"],
                               score_computations=['precursormzmatch'],
                               )
    pipeline = Pipeline(workflow)
    pipeline.query_filters = ["add_fingerprint"]
    pipeline.reference_filters = ["add_fingerprint"]
    pipeline.score_computations = [["modifiedcosine", {"tolerance": 10.0}]]
    pipeline.run(spectrums_file_msp, spectrums_file_msp)
    assert len(pipeline.spectrums_queries[0].get("fingerprint")) == 2048, \
        "The query filters were not modified correctly"
    assert len(pipeline.spectrums_references[0].get("fingerprint")) == 2048, \
        "The reference filters were not modified correctly"
    assert pipeline.scores.score_names == ('ModifiedCosine_score', 'ModifiedCosine_matches')
    all_scores = pipeline.scores.to_array()
    expected = np.array([[1., 0.30384404],
                         [0.30384404, 1.]])
    assert np.allclose(all_scores["ModifiedCosine_score"][3:, 3:], expected)
