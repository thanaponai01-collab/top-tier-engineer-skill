class PrinterError(Exception):
    pass


class PrinterBusy(Exception):
    pass


class PrintJob:
    """Drives the one printer. `start` sends an order and reports whether it printed."""

    def __init__(self, printer):
        self.printer = printer
        self.printing = False
        self.finished = False
        self.error = None

    def start(self, order):
        if self.printing:
            raise PrinterBusy("printer is busy")
        self.printing = True
        self.finished = False
        self.error = None
        try:
            self.printer.send(order.id, order.pages)
        except PrinterError as e:
            self.error = str(e)
            return False
        self.printing = False
        self.finished = True
        return True

    def describe(self):
        if self.error:
            return f"error: {self.error}"
        if self.printing:
            return "printing"
        if self.finished:
            return "finished"
        return "idle"
