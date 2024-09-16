class CCQSentence:
    def __init__(self, sentence, answer):
        self._sentence = sentence
        self._answer = answer

    def isTrue(self):
        if self._answer == "Yes":
            return True
        else:
            return False

    def sentence(self):
        return self._sentence

    def lightFormat(self):
        return self._sentence, self._answer
