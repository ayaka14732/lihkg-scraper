import threading

class ResultWriter:
    def __init__(self):
        self.lock = threading.Lock()
        self.f = open('result.txt', 'a')

    def write_lines(self, lines):
        if lines:
            with self.lock:
                for line in lines:
                    print(line, file=self.f)
