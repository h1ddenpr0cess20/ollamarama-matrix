from ollamarama.thinking import split_thinking


def test_strips_think_tags():
    visible, thinking = split_thinking("<think>planning</think>Hello")
    assert visible == "Hello"
    assert thinking == "planning"


def test_strips_begin_of_thought():
    visible, thinking = split_thinking("<|begin_of_thought|>reason<|end_of_thought|>answer")
    assert visible == "answer"
    assert thinking == "reason"


def test_extracts_solution_block():
    visible, _ = split_thinking("noise <|begin_of_solution|>the answer<|end_of_solution|> trailing")
    assert visible == "the answer"


def test_all_markers_combined():
    text = (
        "<think>plan</think> Hello <|begin_of_thought|>inner<|end_of_thought|>"
        " <|begin_of_solution|>final answer<|end_of_solution|>"
    )
    visible, thinking = split_thinking(text)
    assert visible == "final answer"
    assert "plan" in thinking


def test_none_is_safe():
    assert split_thinking(None) == ("", "")


def test_plain_text_untouched_and_trimmed():
    assert split_thinking("  just text  ") == ("just text", "")


def test_partial_marker_left_alone():
    # An opening tag with no closing tag must not be stripped
    visible, thinking = split_thinking("<think>oops no close")
    assert visible == "<think>oops no close"
    assert thinking == ""
