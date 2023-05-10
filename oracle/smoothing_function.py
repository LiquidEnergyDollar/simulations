import math

class SmoothingFunction:
    def __init__(self, smoothing_factor):
        self.smoothing_factor = smoothing_factor
    def apply_smoothing(self, new_value):
        pass

class ExponentialMovingAverage(SmoothingFunction):
    #EMA Smoothing
    def apply_smoothing(self, new_value):
        if not hasattr(self, 'old_value'):
            self.old_value = new_value
            return new_value
        delta = new_value - self.old_value
        change = delta / self.smoothing_factor
        self.old_value = self.old_value + change
        return self.old_value

class HullMovingAverage(SmoothingFunction):
    def __init__(self, smoothing_factor):
        super().__init__(smoothing_factor)
        self.ema = ExponentialMovingAverage(smoothing_factor)
        self.half_ema = ExponentialMovingAverage(smoothing_factor/2)
        self.hma = ExponentialMovingAverage(math.sqrt(smoothing_factor))
    #HMA Smoothing
    def apply_smoothing(self, new_value):
        ema = self.ema.apply_smoothing(new_value)
        half_ema = self.half_ema.apply_smoothing(new_value)
        raw_hma = 2 * half_ema - ema
        return self.hma.apply_smoothing(raw_hma)