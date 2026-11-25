from app.services.ocr import parse_words


def test_parse_words():
    data = dict(text=['', 'Invoice', '123'], conf=['-1', '95.5', '80.5'],
                left=[0, 10, 50], top=[0, 10, 10], width=[0, 30, 20], height=[0, 10, 10],
                block_num=[0, 1, 1], par_num=[0, 1, 1], line_num=[0, 1, 1])
    result = parse_words(data)
    assert result.text == 'Invoice 123'
    assert result.mean_confidence == 88
    assert result.words[0].left == 10


def test_empty_words():
    result = parse_words({'text': []})
    assert result.text == ''
    assert result.mean_confidence is None
