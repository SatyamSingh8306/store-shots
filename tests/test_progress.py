import io

from store_shots.infrastructure.progress import StageProgress


class PlainStream(io.StringIO):
    def isatty(self) -> bool:
        return False


def test_redirected_output_prints_stage_lines() -> None:
    stream = PlainStream()
    progress = StageProgress(stream)

    progress.update("discovering screens")
    progress.tick()
    progress.finish("done")

    output = stream.getvalue()
    assert "[..] discovering screens" in output
    assert "[done] done in" in output
    assert "\r" not in output
