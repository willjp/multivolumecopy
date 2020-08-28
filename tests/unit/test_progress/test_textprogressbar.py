from multivolumecopy.progress import textprogressbar


class TestTextProgressBar:
    def test_percentage_when_total_is_0(self):
        progress = textprogressbar.TextProgressBar()
        progress.update(index=0, lastindex=0)
        assert progress.percent == 0.0

    def test_percentage_when_total_is_not_0(self):
        progress = textprogressbar.TextProgressBar()
        progress.update(index=5, lastindex=10)
        assert progress.percent == 50.0

    def test_formatting(self):
        progress = textprogressbar.TextProgressBar()
        progress.update(index=5, lastindex=25)
        result = progress.format()
        assert result == '#####                    '


