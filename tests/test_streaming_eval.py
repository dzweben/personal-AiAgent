from agent.evaluate import EvalCase, run_eval
from agent.streaming import CollectingHandler, make_stream_handler


def test_collecting_handler():
    col = CollectingHandler()
    col("a")
    col("b")
    assert col.text == "ab"


def test_stream_handler_routes_tokens():
    col = CollectingHandler()
    handler = make_stream_handler(on_token=col)
    assert handler is not None
    handler.on_llm_new_token("hello ")
    handler.on_llm_new_token("world")
    assert col.text == "hello world"


class _FakeStructured:
    sources = ["a", "b", "c"]
    tools_used = ["search", "wikipedia"]


class _FakeResult:
    structured = _FakeStructured()
    output_text = "green tea is full of antioxidants and helps the heart"


class _FakeAgent:
    def research(self, query):
        return _FakeResult()


def test_eval_report_metrics():
    cases = [
        EvalCase("benefits of green tea", expect_keywords=["antioxidants", "heart", "nope"]),
        EvalCase("another query"),
    ]
    report = run_eval(_FakeAgent(), cases)
    assert len(report.results) == 2
    assert report.parse_rate == 1.0
    assert report.avg_sources == 3.0
    assert report.results[0].keyword_hits == 2
    assert "parse rate" in report.summary()


def test_eval_handles_errors():
    class _Boom:
        def research(self, query):
            raise RuntimeError("kaboom")

    report = run_eval(_Boom(), [EvalCase("x")])
    assert report.parse_rate == 0.0
    assert report.results[0].error is not None
