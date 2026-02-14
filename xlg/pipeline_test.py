"""Pipeline engine tests."""

from xlg.pipeline import run_pipeline


def test_run_pipeline_single():
    def source():
        yield "hello"

    result = list(run_pipeline([source]))
    assert result == ["hello"]


def test_run_pipeline_chain():
    def source():
        yield 1
        yield 2

    def double(upstream):
        for item in upstream:
            yield item * 2

    result = list(run_pipeline([source, double]))
    assert result == [2, 4]
