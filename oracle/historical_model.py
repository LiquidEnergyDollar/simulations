from base_model import BaseModel

class HistoricalModel(BaseModel):

    def get_initial_state(self):
        return {
            'btc_diff': self.btc_diff_data[0],
            'btc_price': self.btc_price_data[0],
            'btc_blockreward': self.btc_blockreward_data[0],
            'kdiff': self.btc_diff_data[0] // 2,
            'kdiff_smoothed': self.btc_diff_data[0] // 2,
            'blockreward_smoothed': self.btc_price_data[0] * self.btc_blockreward_data[0],
            'led_price': 1
        }
