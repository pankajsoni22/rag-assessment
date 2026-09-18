from frontend import ui


def test_theme_hides_the_uploader_size_limit_line():
    assert 'stFileUploaderDropzoneInstructions"] { display: none; }' in ui._CSS
