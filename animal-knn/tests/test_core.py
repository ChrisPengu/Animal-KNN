import io

import joblib
import numpy as np
import pytest
from PIL import Image
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import Normalizer, StandardScaler

from animal_knn.common import read_image
from animal_knn.common import require_unopened_test
from animal_knn.features import canonical, handcrafted, segment
from animal_knn.training import votes


def test_rgb_histogram_and_finite_shape():
    red = np.zeros((96, 96, 3), dtype=np.uint8)
    red[..., 0] = 255
    vector, failed = handcrafted(red)
    assert vector.shape == (512 + 4356,)
    assert vector[:512].argmax() == 63
    assert vector[:512].sum() == pytest.approx(1)
    assert np.isfinite(vector).all()
    assert not failed


def test_segmentation_fallback_has_valid_shape_features():
    pixels = np.full((96, 96, 3), 127, np.uint8)
    output, mask, fallback = segment(pixels)
    assert fallback and np.array_equal(output, pixels)
    assert mask.all()
    feature, fallback = handcrafted(pixels, segmented=True, hu=True)
    assert fallback and np.isfinite(feature).all()
    assert np.array_equal(feature[-7:], np.zeros(7))


@pytest.mark.parametrize("mode", ["L", "RGBA", "P"])
def test_image_modes(mode):
    image = Image.new(mode, (31, 47))
    file = io.BytesIO()
    image.save(file, "PNG")
    file.seek(0)
    result = read_image(file)
    assert result.mode == "RGB"
    assert canonical(result).shape == (96, 96, 3)


def test_corrupt_image_is_readable_error():
    with pytest.raises(ValueError, match="Không đọc được"):
        read_image(io.BytesIO(b"not an image"))


def test_transparency_is_composited_on_white():
    file=io.BytesIO()
    Image.new("RGBA",(2,2),(255,0,0,128)).save(file,"PNG")
    file.seek(0)
    assert read_image(file).getpixel((0,0)) == (255,127,127)
    assert read_image(Image.new("RGBA",(2,2),(255,0,0,128))).getpixel((0,0)) == (255,127,127)


@pytest.mark.parametrize("weights", ["uniform", "distance"])
def test_search_votes_match_sklearn_including_zero_distance(weights):
    x = np.array([[0., 0.], [0., 0.], [1., 0.], [0., 2.]])
    y = np.array([0, 1, 1, 2])
    query = np.array([[0., 0.], [.2, .3]])
    model = KNeighborsClassifier(3, weights=weights).fit(x, y)
    distance, idx = model.kneighbors(query)
    actual = votes(distance, y[idx], 3, weights, n_classes=3)
    np.testing.assert_allclose(actual, model.predict_proba(query))


def test_training_only_transform_and_serialization(tmp_path):
    train = np.array([[0., 1.], [0., 2.], [10., 2.], [10., 1.]])
    validation = np.array([[1000., 1000.]])
    pipeline = Pipeline([("scale", StandardScaler()), ("normalize", Normalizer()), ("knn", KNeighborsClassifier(1))])
    pipeline.fit(train, [0, 0, 1, 1])
    pipeline.predict(validation)
    np.testing.assert_allclose(pipeline["scale"].mean_, train.mean(0))
    output = tmp_path / "model.joblib"
    joblib.dump(pipeline, output)
    np.testing.assert_array_equal(pipeline.predict(train), joblib.load(output).predict(train))


def test_study_cannot_retune_after_test(tmp_path):
    require_unopened_test(tmp_path)
    (tmp_path / "results").mkdir()
    (tmp_path / "results/test_access_receipt.json").write_text("{}")
    with pytest.raises(RuntimeError, match="frozen"):
        require_unopened_test(tmp_path)
