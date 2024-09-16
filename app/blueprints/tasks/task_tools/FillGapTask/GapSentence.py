class GapSentence:
    def __init__(self, start: str, end: str, ans: str):
        self._sentence_start = start
        self._sentence_end = end
        self._answer = ans

    def start(self):
        return self._sentence_start

    def end(self):
        return self._sentence_end

    def answer(self):
        return self._answer

