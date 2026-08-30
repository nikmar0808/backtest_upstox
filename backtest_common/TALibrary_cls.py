import logging
import pandas as pd
import numpy as np 
import math
from backtest_common import __backtestconfig__

# Create and configure logger
ta_library_logger = logging.getLogger("logs/ta_library.log")
ta_library_logger.addHandler(logging.FileHandler("logs/ta_library.log", mode='a'))
ta_library_logger.setLevel(logging.INFO)

class TALibrary:

    def __init__(self,broker,logger=ta_library_logger): 
        self.broker=broker
        self.logger=logger

    # Round to the nearest multiple of 'a' with two decimal places and truc to 2 decimal places
    def round_nearest(self, x, a):
        tr_vals = np.asarray(x, dtype=np.float64)
        tr_vals = np.trunc(np.round(tr_vals / a) * a * 100)
        return pd.Series(tr_vals/100)

    def calc_gaussian_ma(self, source_series:pd.Series, length=13, ema_length=8, adaptive=True, volatility_period=3, standard_deviation_override=1.0):
        """
        Calculates the Gaussian Moving Average.

        Args:
            source_series (pd.Series or np.array): Series of close prices.
            length (int): Length for the Gaussian Moving Average calculation. Defaults to 8.
            adaptive (bool): Whether to use adaptive standard deviation or a fixed value. Defaults to True.
            volatility_period (int): Period for calculating standard deviation if 'adaptive' is True. Defaults to 3.
            standard_deviation_override (float): Fixed standard deviation value if 'adaptive' is False. Defaults to 1.0.

        Returns:
            pd.Series: A series of Gaussian Moving Average values.

        Sample Call:
            gma_results = gaussian_ma(df['close'], length=13, adaptive=True, volatility_period=3, standard_deviation_override=1.0)

        """

        gma_values = []

        # Ensure source_series is a Pandas Series for easier rolling window operations
        if not isinstance(source_series, pd.Series):
            source_series = pd.Series(source_series)

        for i in range(len(source_series)):
            current_gma = 0.0
            sum_of_weights = 0.0

            # Determine sigma (standard deviation) based on 'adaptive' parameter
            # If adaptive is True, the standard deviation (sigma) is calculated using a rolling window of the source_series,
            # similar to Pine Script's ta.stdev function.
            # If adaptive is False, a fixed standard_deviation_override value is used.
            if adaptive:
                if i >= volatility_period - 1:
                    sigma = source_series.iloc[i - volatility_period + 1 : i + 1].std()
                else:
                    sigma = 0.1
            else:
                sigma = standard_deviation_override

            # # Small default values and checks for zero sigma are included to prevent division errors for potential zero sigma.
            if sigma == 0:
                sigma = 0.1
            
            # The for loop iterates through the data points, calculating the weighted sum of (highest + lowest) over a specific period,
            # where the weights are determined by the Gaussian function.
            # Highest and Lowest for the current window are found using max() and min() on the appropriate slice of source_series.
            # np.exp() and np.pow() are used for the mathematical operations in the Gaussian weight calculation.
            for j in range(length):
                # Calculate weight using the Gaussian formula
                weight = np.exp(-((j - (length - 1)) / (2 * sigma))**2 / 2)

                # Ensure sufficient historical data for 'highest' and 'lowest' calculations
                if i - (j + 1) + 1 >= 0:
                    value = source_series.iloc[i - (j + 1) + 1 : i + 1].max() + source_series.iloc[i - (j + 1) + 1 : i + 1].min()
                else:
                    value = source_series.iloc[i] * 2

                current_gma += (value * weight)
                sum_of_weights += weight

            # Avoid division by zero and calculate initial gma_values
            if sum_of_weights == 0:
                gma_values.append(current_gma)
            else:
                gma_values.append((current_gma / sum_of_weights) / 2)

        gma_series = pd.Series(gma_values, index=source_series.index)

        # Apply an Exponential Moving Average (EMA) using Pandas' .ewm() method, which functions similarly to Pine Script's ta.ema.
        # adjust=False ensures it behaves similarly to Pine Script's EMA calculation.
        final_gma = gma_series.ewm(span=ema_length, adjust=False).mean()

        return final_gma

    # ATR (Average True Range) calculation
    def calc_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.DataFrame:
        """Calculates vectorised Average True Range (ATR) using RMA smoothing."""
        if min(len(high), len(low), len(close)) <= length:
            self._logger.exception(f"Not enough data for atr calculations - {str(len(close))}")
            raise ValueError(f"Not enough data for atr calculations: - {str(len(close))}")
            
        hl = high - low
        hc = (high - close.shift(1)).abs()
        lc = (low - close.shift(1)).abs()
        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        
        # Smooth using your clean vectorised RMA function logic
        atr = tr.ewm(alpha=1/length, min_periods=length, adjust=False).mean()
        
        df_atr = pd.DataFrame({"atr": atr})
        return df_atr

    # ATR Trailing Stop loss calculation
    # default settings is 13
    def calc_atr_tsl(self, df: pd.DataFrame, atr_multiplier: float) -> pd.DataFrame:

        df_atr = pd.DataFrame()

        df_atr['atr_stop_long'] = 0.0
        df_atr['atr_stop_short'] = 0.0

        # Initialize the first stop-loss (example for long position)
        # This assumes you have an entry point or are starting from the beginning of your data
        # For a real-time scenario, you'd update this based on your trade entry.
        if len(df) > 0:

            df_atr.loc[0, 'atr_stop_long'] = df['open'].iloc[0] - (df['exit_atr'].iloc[0] * atr_multiplier)
            df_atr.loc[0, 'atr_stop_short'] = df['open'].iloc[0] + (df['exit_atr'].iloc[0] * atr_multiplier)

        for i in range(1, len(df)):
            # Trailing Stop for Long Position
            # It moves up with price, but never down
            current_atr_stop_long = df['high'].iloc[i-1] - (df['exit_atr'].iloc[i-1] * atr_multiplier)
            df_atr.loc[i, 'atr_stop_long'] = max(current_atr_stop_long, df_atr['atr_stop_long'].iloc[i-1])

            # Trailing Stop for Short Position
            # It moves down with price, but never up
            current_atr_stop_short = df['low'].iloc[i-1] + (df['exit_atr'].iloc[i-1] * atr_multiplier)
            df_atr.loc[i, 'atr_stop_short'] = min(current_atr_stop_short, df_atr['atr_stop_short'].iloc[i-1])

        return df_atr
        
    def calc_supertrend(self, high: pd.Series, low: pd.Series, close: pd.Series, length: int = 7, multiplier: float = 3.0) -> pd.DataFrame:
        """
        Highly optimized, production-grade vectorised Supertrend engine.
        Pre-allocates contiguous memory blocks to calculate 1min Nifty/BankNifty frames instantly.
        """
        if min(len(high), len(low), len(close)) <= length:
            self._logger.exception(f"Not enough data for supertrend calculations - {str(len(close))}")
            raise ValueError(f"Not enough data for supertrend calculations: - {str(len(close))}")
            
        # Get clean vectorised ATR series array
        df_atr = self.calc_atr(high, low, close, length=length)
        atr_arr = df_atr["atr"].values
        
        high_arr = high.values
        low_arr = low.values
        close_arr = close.values
        
        hl2_arr = (high_arr + low_arr) / 2
        basic_ub = hl2_arr + (multiplier * atr_arr)
        basic_lb = hl2_arr - (multiplier * atr_arr)
        
        size = len(close)
        final_ub = np.zeros(size)
        final_lb = np.zeros(size)
        supert = np.zeros(size)
        direction = np.ones(size)
        
        # Highly performance-optimized continuous array loop 
        for i in range(1, size):
            # Calculate Upper Band
            if basic_ub[i] < final_ub[i-1] or close_arr[i-1] > final_ub[i-1]:
                final_ub[i] = basic_ub[i]
            else:
                final_ub[i] = final_ub[i-1]
                
            # Calculate Lower Band
            if basic_lb[i] > final_lb[i-1] or close_arr[i-1] < final_lb[i-1]:
                final_lb[i] = basic_lb[i]
            else:
                final_lb[i] = final_lb[i-1]
                
            # Trailing direction evaluation matrices
            if direction[i-1] == 1:
                if close_arr[i] < final_lb[i]:
                    direction[i] = -1
                    supert[i] = final_ub[i]
                else:
                    direction[i] = 1
                    supert[i] = final_lb[i]
            else:
                if close_arr[i] > final_ub[i]:
                    direction[i] = 1
                    supert[i] = final_lb[i]
                else:
                    direction[i] = -1
                    supert[i] = final_ub[i]
                    
        # Mask bands based on active trends to replicate pandas-ta exactly
        st_lb_masked = np.where(direction == 1, final_lb, np.nan)
        st_ub_masked = np.where(direction == -1, final_ub, np.nan)
        
        df_st = pd.DataFrame({
            "st_val": supert,
            "st_dir": direction,
            "st_lb": st_lb_masked,
            "st_ub": st_ub_masked
        }, index=close.index)
        
        return df_st

    def pivothigh(series, left_bars, right_bars):
        """
        A pivot high occurs when the high is the highest over a window of bars.
        """
        ph_values = pd.Series(np.nan, index=series.index)
        for i in range(left_bars, len(series) - right_bars):
            if series.iloc[i] == series.iloc[i - left_bars : i + right_bars + 1].max():
                ph_values.iloc[i] = series.iloc[i]
        return ph_values

    def pivotlow(series, left_bars, right_bars):
        """
        A pivot low occurs when the low is the lowest over a window of bars.
        """
        pl_values = pd.Series(np.nan, index=series.index)
        for i in range(left_bars, len(series) - right_bars):
            if series.iloc[i] == series.iloc[i - left_bars : i + right_bars + 1].min():
                pl_values.iloc[i] = series.iloc[i]
        return pl_values

    """
    def pivotpoint_supertrend(high_series, low_series, close_series, prd=3, factor=2.0, atr_period=25):
        """
    """
        Calculates the Pivot Point Supertrend indicator.

        Args:
            high_series (pd.Series): Series of high prices.
            low_series (pd.Series): Series of low prices.
            close_series (pd.Series): Series of close prices.
            prd (int): Pivot Point Period. Defaults to 3.
            factor (float): ATR Factor. Defaults to 2.0.
            atr_period (int): ATR Period. Defaults to 25.

        Returns:
            pd.DataFrame: DataFrame containing Supertrend, Trend, Center Line,
                        Support, Resistance, Buy Signals, and Sell Signals.

        Sample Call:
        df_st = pivotpoint_supertrend(df['high'], df['low'], df['close'],
                                        prd=3, factor=2.0, atr_period=25)
        print(df_st[['close', 'Trailingsl', 'Trend', 'BuySignal', 'SellSignal'].tail())

        """
    """

        df = pd.DataFrame({'high': high_series, 'low': low_series, 'close': close_series})

        # Calculate Pivot High/Low
        df['ph'] = pivothigh(df['high'], prd, prd)
        df['pl'] = pivotlow(df['low'], prd, prd)

        # Calculate the Center line using pivot points
        center_line = pd.Series(np.nan, index=df.index)
        last_pp = np.nan
        for i in range(len(df)):
            if not pd.isna(df['ph'].iloc[i]):
                last_pp = df['ph'].iloc[i]
            elif not pd.isna(df['pl'].iloc[i]):
                last_pp = df['pl'].iloc[i]

            if not pd.isna(last_pp):
                if pd.isna(center_line.iloc[i-1]): # first calculation
                    center_line.iloc[i] = last_pp
                else: # weighted calculation
                    center_line.iloc[i] = (center_line.iloc[i-1] * 2 + last_pp) / 3
            
            # Carry forward the previous center line if no new pivot point is found
            if pd.isna(center_line.iloc[i]) and i > 0:
                center_line.iloc[i] = center_line.iloc[i-1]
            
        df['center'] = center_line

        # Calculate ATR
        df['tr0'] = abs(df['high'] - df['low'])
        df['tr1'] = abs(df['high'] - df['close'].shift(1))
        df['tr2'] = abs(df['low'] - df['close'].shift(1))
        df['TR'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
        df['ATR'] = df['TR'].ewm(span=atr_period, adjust=False).mean() # Using EMA like Wilder's Smoothing for ATR


        # Upper/lower bands calculation
        df['Up'] = df['center'] - (factor * df['ATR'])
        df['Dn'] = df['center'] + (factor * df['ATR'])

        # Get the trend
        df['TUp'] = np.nan
        df['TDown'] = np.nan
        df['Trend'] = 0

        for i in range(1, len(df)):
            if df['close'].iloc[i-1] > df['TUp'].iloc[i-1]:
                df['TUp'].iloc[i] = max(df['Up'].iloc[i], df['TUp'].iloc[i-1])
            else:
                df['TUp'].iloc[i] = df['Up'].iloc[i]

            if df['close'].iloc[i-1] < df['TDown'].iloc[i-1]:
                df['TDown'].iloc[i] = min(df['Dn'].iloc[i], df['TDown'].iloc[i-1])
            else:
                df['TDown'].iloc[i] = df['Dn'].iloc[i]

            if df['close'].iloc[i] > df['TDown'].iloc[i-1]:
                df['Trend'].iloc[i] = 1
            elif df['close'].iloc[i] < df['TUp'].iloc[i-1]:
                df['Trend'].iloc[i] = -1
            else:
                df['Trend'].iloc[i] = df['Trend'].iloc[i-1]

        df['Trailingsl'] = df.apply(lambda row: row['TUp'] if row['Trend'] == 1 else row['TDown'], axis=1)

        # Check and plot the signals
        df['BuySignal'] = ((df['Trend'] == 1) & (df['Trend'].shift(1) == -1)).astype(int)
        df['SellSignal'] = ((df['Trend'] == -1) & (df['Trend'].shift(1) == 1)).astype(int)
        
        return df
        """

    # MACD (Moving Average Convergance Divergence) calculations
    # default settings are (26, 12, 9)
    def calc_macd(self, close: pd.Series, fast: int = 12, 
                  slow: int = 26, signal: int = 9) -> pd.DataFrame:
        
        min_len = max(fast, slow, signal)
        if len(close) <= min_len:
            self._logger.exception(f"Not enough data for macd calculations - {str(len(close))}")
            raise ValueError(f"Not enough data for macd calculations: - {str(len(close))}")

        fastma = close.ewm(span=fast, min_periods=fast).mean()
        slowma = close.ewm(span=slow, min_periods=slow).mean()
        macd = fastma - slowma
        signalma = macd.ewm(span=signal, min_periods=signal).mean() 
        histogram = macd - signalma

        data = {
            "macd": macd,
            "macdh": histogram,
            "macds": signalma
        }

        df_macd = pd.DataFrame(data)

        return df_macd


    # PPO (Percentage Price Oscillator) calculations
    # default settings are (26, 12, 9)
    def calc_ppo(self, close: pd.Series, fast: int = 12,
                 slow: int = 26, signal: int = 9) -> pd.DataFrame:
        
        min_len = max(fast, slow, signal)
        if len(close) <= min_len:
            self._logger.exception(f"Not enough data for ppo calculations - {str(len(close))}")
            raise ValueError(f"Not enough data for ppo calculations: - {str(len(close))}")

        fastma = close.ewm(span=fast, min_periods=fast).mean()
        slowma = close.ewm(span=slow, min_periods=slow).mean()
        ppo = (fastma - slowma) * 100 / slowma
        signalma = ppo.ewm(span=signal, min_periods=signal).mean() 
        histogram = ppo - signalma

        data = {
            "ppo": ppo,
            "ppoh": histogram,
            "ppos": signalma
        }

        df_ppo = pd.DataFrame(data)

        return df_ppo


    # ADX (Average Directional Index) calculations
    # default settings is 14
    def calc_adx(self, high: pd.Series, low: pd.Series, close: pd.Series,
                 length: int = 14, lensig: int = 14) -> pd.DataFrame:
        
        if ((len(close) != len(high)) or (len(close) != len(low))) :
            self._logger.exception(f"Mismatch in series length for adx - {str(len(high))}" 
                                  +f" / {str(len(low))} / {str(len(close))}")
            raise ValueError(f"Mismatch in series length for adx - {str(len(high))}" 
                            +f" / {str(len(low))} / {str(len(close))}")
        
        if (len(close) <= length) :
            self._logger.exception(f"Not enough data for adx calculations - {str(len(close))}")
            raise ValueError(f"Not enough data for adx calculations: - {str(len(close))}")

        df_atr = self.calc_atr(high, low, close, length)
        atr = df_atr["atr"]

        up = high - high.shift()
        dn = low.shift() - low 

        pos = ((up > dn) & (up > 0)) * up
        neg = ((dn > up) & (dn > 0)) * dn

        dmp = pos.ewm(alpha=(1.0/length), min_periods=length).mean() * 100 / atr
        dmn = neg.ewm(alpha=(1.0/length), min_periods=length).mean() * 100 / atr

        dx = (dmp - dmn).abs() / (dmp + dmn) * 100
        adx = dx.ewm(alpha=(1.0/lensig), min_periods=lensig).mean()

        data = {
            "adx": adx, 
            "dm_pos": dmp, 
            "dm_neg": dmn
        }

        df_adx = pd.DataFrame(data)

        return df_adx


    # STOCH (Stochastic Oscillator) calculations
    # default settings is 14
    def calc_stoch(self, high: pd.Series, low: pd.Series, close: pd.Series,
                   k_len: int = 14, smooth_k: int = 3, d_len: int = 3) -> pd.DataFrame:
        
        if ((len(close) != len(high)) or (len(close) != len(low))) :
            self._logger.exception(f"Mismatch in series length for STOCH - {str(len(high))}" 
                                  +f" / {str(len(low))} / {str(len(close))}")
            raise ValueError(f"Mismatch in series length for STOCH - {str(len(high))}" 
                            +f" / {str(len(low))} / {str(len(close))}")
        
        if (len(close) <= max(k_len, smooth_k, d_len)) :
            self._logger.exception(f"Not enough data for STOCH calculations - {str(len(close))}")
            raise ValueError(f"Not enough data for STOCH calculations: - {str(len(close))}")

        lowest_low = low.rolling(k_len, min_periods=k_len).min()
        highest_high = high.rolling(k_len, min_periods=k_len).max()

        stoch = 100 * (close - lowest_low) / (highest_high - lowest_low)

        stoch_k = stoch.ewm(span=smooth_k, min_periods=smooth_k).mean()
        stoch_d = stoch_k.ewm(span=d_len, min_periods=d_len).mean()

        data = {
            "stoch_k": stoch_k,
            "stoch_d": stoch_d
        }

        df_stoch = pd.DataFrame(data)

        return df_stoch


    # ATR (Average True Range) calculation
    # default settings is 13
    def calc_atr(self, high: pd.Series, low: pd.Series, close: pd.Series,
                 length: int = 13, length2: int = None) -> pd.DataFrame:
        
        if ((len(close) != len(high)) or (len(close) != len(low))) :
            self._logger.exception(f"Mismatch in series length for atr - {str(len(high))}" 
                                  +f" / {str(len(low))} / {str(len(close))}")
            raise ValueError(f"Mismatch in series length for atr - {str(len(high))}" 
                            +f" / {str(len(low))} / {str(len(close))}")
        
        if (len(close) <= length) :
            self._logger.exception(f"Not enough data for atr calculations - {str(len(close))}")
            raise ValueError(f"Not enough data for atr calculations: - {str(len(close))}")

        p_close = close.shift()
        hl_range = high - low
        h_p_close = (high - p_close).abs()
        p_close_l = (p_close - low).abs()

        tr = pd.concat([hl_range, h_p_close, p_close_l], axis=1)
        tr = tr.max(axis=1)

        if length2 is None:
            atr = tr.ewm(alpha=(1.0/length), min_periods=length).mean()
            atr_std = tr.ewm(alpha=(1.0/length), min_periods=length).std()
            data = {
                "atr": atr,
                "atr_std": atr_std
            }
        else:
            atr_fast = tr.ewm(alpha=(1.0/length), min_periods=length).mean()
            atr_slow = tr.ewm(alpha=(1.0/length2), min_periods=length2).mean()
            data = {
                "atr_fast": atr_fast,
                "atr_slow": atr_slow
            }

        df_atr = pd.DataFrame(data)

        return df_atr

    # RSI (Relative Strength Index) calculations
    # default settings is 14
    def calc_rsi(self, close: pd.Series, length: int = 14) -> pd.DataFrame:
        
        if len(close) <= length:
            self._logger.exception(f"Not enough data for rsi calculations - {str(len(close))}")
            raise ValueError(f"Not enough data for rsi calculations: - {str(len(close))}")

        negative = close.diff()
        positive = negative.copy()
        positive[positive < 0] = 0 
        negative[negative > 0] = 0
        positive_avg = positive.ewm(alpha=(1.0/length), min_periods=length).mean()
        negative_avg = negative.ewm(alpha=(1.0/length), min_periods=length).mean()
        rsi = 100 * positive_avg / (positive_avg + negative_avg.abs())

        data = {
            "rsi": rsi
        }

        df_rsi = pd.DataFrame(data)

        return df_rsi


    # EMA (Exponential Moving Average) calculations
    # default settings is 10
    def calc_ema(self, close: pd.Series, length: int = 10) -> pd.DataFrame:
        
        if len(close) <= length:
            self._logger.exception(f"Not enough data for ema calculations - {str(len(close))}")
            raise ValueError(f"Not enough data for ema calculations: - {str(len(close))}")

        ema = close.ewm(span=length, min_periods=length).mean()

        data = {
            "ema": ema
        }

        df_ema = pd.DataFrame(data)

        return df_ema

    def calc_rma(self, close: pd.Series, length: int = 14) -> pd.DataFrame:
        """Calculates fully vectorised Running Moving Average (RMA)."""
        if len(close) <= length:
            self._logger.exception(f"Not enough data for rma calculations - {str(len(close))}")
            raise ValueError(f"Not enough data for rma calculations: - {str(len(close))}")
            
        rma = close.ewm(alpha=1/length, min_periods=length, adjust=False).mean()
        
        df_rma = pd.DataFrame({"rma": rma})
        return df_rma

    # ROC (Rate of Change) calculations
    # default settings is 3
    def calc_roc(self, close: pd.Series, length: int = 3, ret_percent: bool = True) -> pd.DataFrame:
        
        if len(close) <= length:
            self._logger.exception(f"Not enough data for roc calculations - {str(len(close))}")
            raise ValueError(f"Not enough data for roc calculations: - {str(len(close))}")

        roc = close.diff(length)
        if ret_percent:
           roc = roc / close.shift(length) 

        data = {
            "roc": roc
        }

        df_roc = pd.DataFrame(data)

        return df_roc


    # BB (Bollinger Bands) calculations
    # default settings are (20, 1)
    def calc_bb(self, close: pd.Series, long_length: int = 20, short_length: int = 20, 
                entry_long_std: int = None, entry_short_std: int = None,
                exit_long_std: int = None, exit_short_std: int = None) -> pd.DataFrame:
        
        if (len(close) <= long_length) or (len(close) <= short_length):
            self._logger.exception(f"Not enough data for bb calculations - {str(len(close))}")
            raise ValueError(f"Not enough data for bb calculations: - {str(len(close))}")

        if (entry_long_std is None) and (entry_short_std is not None):
             entry_long_std = entry_short_std
        if (entry_long_std is not None) and (entry_short_std is None):
             entry_short_std = entry_long_std
        if (exit_long_std is None) and (exit_short_std is not None):
             exit_long_std = exit_short_std
        if (entry_long_std is not None) and (entry_short_std is None):
             exit_short_std = exit_long_std
        
        bblongmid = close.ewm(alpha=(1.0/long_length), min_periods=long_length).mean()
        bblongstd = close.ewm(alpha=(1.0/long_length), min_periods=long_length).std()

        if long_length == short_length:
            bbshortmid = bblongmid
            bbshortstd = bblongstd
        else:
            bbshortmid = close.ewm(alpha=(1.0/short_length), min_periods=short_length).mean()
            bbshortstd = close.ewm(alpha=(1.0/short_length), min_periods=short_length).std()

        bbrange = 2 * bblongstd
        data = {
            "bb_long_mid": bblongmid,
            "bb_short_mid": bbshortmid,
            "bb_range": bbrange
        }

        if entry_long_std is not None:
            bblongentry = bblongmid + (entry_long_std * bblongstd)
            bbshortentry = bbshortmid - (entry_short_std * bbshortstd)
            data["bb_long_entry"] = bblongentry
            data["bb_short_entry"] = bbshortentry

        if exit_long_std is not None:
            bblongexit = bblongmid + (exit_long_std * bblongstd)
            bbshortexit = bbshortmid - (exit_short_std * bbshortstd)
            data["bb_long_exit"] = bblongexit
            data["bb_short_exit"] = bbshortexit

        df_bb = pd.DataFrame(data)

        return df_bb


    # CE (Chandelier Exit) calculations
    # default settings is 14
    def calc_ce(self, high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14,
                long_multiplier: int = 2, short_multiplier: int = 2) -> pd.DataFrame:
        
        if ((len(close) != len(high)) or (len(close) != len(low))) :
            self._logger.exception(f"Mismatch in series length for ce - {str(len(high))}" 
                                  +f" / {str(len(low))} / {str(len(close))}")
            raise ValueError(f"Mismatch in series length for ce - {str(len(high))}" 
                            +f" / {str(len(low))} / {str(len(close))}")
  
        if (len(close) <= length) :
            self._logger.exception(f"Not enough data for ce calculations - {str(len(close))}")
            raise ValueError(f"Not enough data for ce calculations: - {str(len(close))}")


        df_atr = self.calc_atr(high, low, close, length)
        atr = df_atr["atr"]

        highest_high = high.rolling(length, min_periods=length).max()
        lowest_low = low.rolling(length, min_periods=length).min()
        long_exit = highest_high - long_multiplier * atr
        short_exit = lowest_low + short_multiplier * atr

        data = {
            "ce_long_exit": long_exit,
            "ce_short_exit": short_exit
        }

        df_ce = pd.DataFrame(data)

        return df_ce


    # KER (Kaufman Efficiency Ratio) calculations
    # default settings is 20
    def calc_ker(self, close: pd.Series, length: int = 20) -> pd.DataFrame:
        
        if len(close) <= length:
            self._logger.exception(f"Not enough data for ker calculations - {str(len(close))}")
            raise ValueError(f"Not enough data for ker calculations: - {str(len(close))}")

        net_change = close.diff(length)
        abs_ind_change = close.diff().abs()
        tot_ind_change = abs_ind_change.rolling(length, min_periods=length).sum()
        ker = net_change / tot_ind_change

        data = {
            "ker": ker
        }

        df_ker = pd.DataFrame(data)

        return df_ker


    # NRIB (Narrow Range w/ Inside Bar) calculations
    # default settings is 14
    def calc_nrib(self, high: pd.Series, low: pd.Series, length: int = 14) -> pd.DataFrame:
        
        if (len(high) != len(low)) :
            self._logger.exception(f"Mismatch in series length for nrib - {str(len(high))}" 
                                  +f" / {str(len(low))} ")
            raise ValueError(f"Mismatch in series length for nrib - {str(len(high))}" 
                            +f" / {str(len(low))} ")

        if (len(high) <= length) :
            self._logger.exception(f"Not enough data for nrib calculations - {str(len(high))}")
            raise ValueError(f"Not enough data for nrib calculations: - {str(len(high))}")


        range = high - low
        range_ma = range.rolling(length, min_periods=length).mean()
    
        prev_high = high.shift()
        prev_low = low.shift()
        ib_flag = ((high < prev_high) & (low > prev_low)) 

        data = {
            "nrib_range": range,
            "nrib_range_ma": range_ma,
            "ib_flag": ib_flag
        }

        df_nrib = pd.DataFrame(data)

        return df_nrib

    # CPR (Central Pivot Range) calculations
    # default length setting is 5
    def calc_cpr(self, high: pd.Series, low: pd.Series, close: pd.Series,
                 length: int = 5) -> pd.DataFrame:
        
        if ((len(close) != len(high)) or (len(close) != len(low))) :
            self._logger.exception(f"Mismatch in series length for cpr - {str(len(high))}" 
                                  +f" / {str(len(low))} / {str(len(close))}")
            raise ValueError(f"Mismatch in series length for cpr - {str(len(high))}" 
                            +f" / {str(len(low))} / {str(len(close))}")

        if (len(close) <= length) :
            self._logger.exception(f"Not enough data for cpr calculations - {str(len(close))}")
            raise ValueError(f"Not enough data for cpr calculations: - {str(len(close))}")

        pivot_point = (high + low + close) / 3
        bottom_point = (high + low) / 2
        top_point = 2 * pivot_point - bottom_point 
        cpr_width = (top_point - bottom_point).abs()
        cpr_width = cpr_width * 1000 / close
        cpr_width_ma = cpr_width.rolling(length, min_periods=length).mean()

        data = {
            "pivot_point": pivot_point,
            "top_point": top_point,
            "bottom_point": bottom_point,
            "cpr_width": cpr_width,
            "cpr_width_ma": cpr_width_ma
        }

        df_cpr = pd.DataFrame(data)

        return df_cpr


    # High Low Range vs atr calculations
    # default settings is 5 & 13
    def calc_hl_range_atr(self, high: pd.Series, low: pd.Series, close: pd.Series,
                          range_length: int = 5, atr_length: int = 13) -> pd.DataFrame:
        
        if ((len(close) != len(high)) or (len(close) != len(low))) :
            self._logger.exception(f"Mismatch in series length for hl range atr - {str(len(high))}" 
                                  +f" / {str(len(low))} / {str(len(close))}")
            raise ValueError(f"Mismatch in series length for hl range atr - {str(len(high))}" 
                            +f" / {str(len(low))} / {str(len(close))}")

        if (len(close) <= range_length)  or (len(close) <= atr_length):
            self._logger.exception(f"Not enough data for hl range atr calculations - {str(len(close))}")
            raise ValueError(f"Not enough data for hl range atr calculations: - {str(len(close))}")

        df_atr = self.calc_atr(high, low, close, atr_length)
        atr = df_atr["atr"]

        highest_high = high.rolling(range_length, min_periods=range_length).max()
        lowest_low = low.rolling(range_length, min_periods=range_length).min()
        hl_range = highest_high - lowest_low

        data = {
            "hl_range": hl_range,
            "hl_range_atr": atr
        }

        df_hlra = pd.DataFrame(data)

        return df_hlra


    # ATR bounds filter - to determine if ATR values in specific range
    # default settings is 13 & 13
    def calc_atr_bounds(self, high: pd.Series, low: pd.Series, close: pd.Series,
                        bounds_length: int = 13, quantile_length: int = 987,
                        min_quantile: float = 0.2, max_quantile: float = 0.8) -> pd.DataFrame:
        
        if ((len(close) != len(high)) or (len(close) != len(low))) :
            self._logger.exception(f"Mismatch in series length for atr bounds - {str(len(high))}" 
                                  +f" / {str(len(low))} / {str(len(close))}")
            raise ValueError(f"Mismatch in series length for atr bounds - {str(len(high))}" 
                            +f" / {str(len(low))} / {str(len(close))}")

        if (len(close) <= bounds_length)  or (len(close) <= quantile_length):
            self._logger.exception(f"Not enough data for atr bounds calculations - {str(len(close))}")
            raise ValueError(f"Not enough data for atr bounds calculations: - {str(len(close))}")

        df_atr = self.calc_atr(high, low, close, bounds_length)
        atr = df_atr["atr"]

        min_val = atr.rolling(quantile_length, min_periods=quantile_length).quantile(min_quantile)
        max_val = atr.rolling(quantile_length, min_periods=quantile_length).quantile(max_quantile)

        data = {
            "atr_ref": atr,
            "atr_min": min_val,
            "atr_max": max_val,
        }

        df_atrb = pd.DataFrame(data)

        return df_atrb


    # Simple Linear Regression - returns either the slope
    # or the next predicted value
    def calc_linreg(self, in_series: pd.Series, linreg_len: int = 5,
                    weighted: bool = False, get_slope: bool = False,
                    predict_val: bool = True):

        if (linreg_len <= 1):
            self._logger.exception(f"Need at least 2 data poiints for linear regression - {str(linreg_len)}")
            raise ValueError(f"Need at least 2 data poiints for linear regression - {str(linreg_len)}")
        
        if (len(in_series) <= linreg_len):
            self._logger.exception(f"Not enough data for linear regression calculations - {str(len(in_series))}")
            raise ValueError(f"Not enough data for linear regression calculations: - {str(len(in_series))}")
        
        x_sum = 0.5 * linreg_len * (linreg_len + 1)
        x2_sum = x_sum * (2 * linreg_len + 1) / 3
        divisor = linreg_len * x2_sum - x_sum * x_sum

        if weighted:
            y_sum = linreg_len * in_series.ewm(span=linreg_len, min_periods=linreg_len).sum()
            xy_sum = linreg_len * in_series.ewm(span=(linreg_len**2), min_periods=linreg_len).sum()
        else:
            y_sum = in_series.rolling(linreg_len, min_periods=linreg_len).sum()
            xy_sum = linreg_len * in_series.ewm(span=linreg_len, min_periods=linreg_len).sum()

        slope = (linreg_len * xy_sum - x_sum * y_sum) / divisor
        if get_slope:
            data = {
                "lr_val": slope,
            }

            df_lr = pd.DataFrame(data)
            return df_lr
        
        intercept = (y_sum * x2_sum - x_sum * xy_sum) / divisor
        if predict_val:
            pred_inp = linreg_len + 1
        else:
            pred_inp = linreg_len

        if weighted:
            pred_val = (slope * pred_inp + intercept) * linreg_len / pred_inp
        else:
            pred_val = slope * pred_inp + intercept

        data = {
            "lr_val": pred_val,
        }

        df_lr = pd.DataFrame(data)

        return df_lr


    # Simple Linear Regression - with smoothening
    def calc_linreg_ema(self, in_series: pd.Series, linreg_len: int = 5,
                        smooth_len:int = 3, weighted: bool = False, 
                        get_slope: bool = False, predict_val: bool = True):

        if (linreg_len <= 1):
            self._logger.exception(f"Need at least 2 data poiints for linear regression - {str(linreg_len)}")
            raise ValueError(f"Need at least 2 data poiints for linear regression - {str(linreg_len)}")
        
        if (len(in_series) <= linreg_len):
            self._logger.exception(f"Not enough data for linear regression calculations - {str(len(in_series))}")
            raise ValueError(f"Not enough data for linear regression calculations: - {str(len(in_series))}")

        df_lr = self.calc_linreg(in_series, linreg_len, weighted, get_slope, predict_val)
        lr_ser = df_lr["lr_val"]

        df_ema = self.calc_ema(lr_ser, smooth_len)
        lr_ema = df_ema["ema"]

        data = {
            "lr_val": lr_ser,
            "lr_ema": lr_ema,
        }

        df_lr_ema = pd.DataFrame(data)

        return df_lr_ema


    # Calculate wick length
    def calc_wick_pct(self, open: pd.Series, high: pd.Series, 
                      low: pd.Series, close: pd.Series):

        if ((len(close) != len(high)) or (len(close) != len(low)) or (len(close) != len(open))) :
            self._logger.exception(f"Mismatch in series length for wick calculations - {str(len(open))}" 
                                  +f" / {str(len(high))} / {str(len(low))} / {str(len(close))}")
            raise ValueError(f"Mismatch in series length for wick calculations - {str(len(open))}" 
                            +f" / {str(len(high))} / {str(len(low))} / {str(len(close))}")

        open_close = pd.concat([open, close], axis=1)
        oc_high = open_close.max(axis=1)
        oc_low = open_close.min(axis=1)
        hl_range = high - low

        top_wick = (high - oc_high) / hl_range
        bot_wick = (oc_low - low) / hl_range

        data = {
            "top_wick": top_wick,
            "bot_wick": bot_wick,
        }

        df_wick_pct = pd.DataFrame(data)

        return df_wick_pct


    # Check for fractals
    def check_fractal(self, high: pd.Series, low: pd.Series,
                      length: int = 5):

        if ((len(high) <= length) or (len(low) <= length)):
            self._logger.exception(f"Not enough data for fractal check - {str(len(high))}")
            raise ValueError(f"Not enough data for fractal check: - {str(len(high))}")

        mid_pt = math.floor(length /  2)

        highest_high = high.rolling(mid_pt, min_periods=mid_pt).max()
        high_fractal = (
            (highest_high.shift(mid_pt + 1) < high.shift(mid_pt))
            & (highest_high < high.shift(mid_pt)) 
        )

        lowest_low = low.rolling(mid_pt, min_periods=mid_pt).min()
        low_fractal = (
            (lowest_low.shift(mid_pt + 1) > low.shift(mid_pt))
            & (lowest_low > low.shift(mid_pt)) 
        )

        data = {
            "high_fractal": high_fractal,
            "low_fractal": low_fractal,
        }

        df_fractal = pd.DataFrame(data)

        return df_fractal

    # STOCH RSI (Stochastic RSI) calculations
    # default settings is 14
    def calc_stoch_rsi(self, close: pd.Series, rsi_len: int = 14,
                       stoch_len: int = 3) -> pd.DataFrame:
        
        if (len(close) <= max(rsi_len, stoch_len)) :
            self._logger.exception(f"Not enough data for STOCH RSI calculatins - {str(len(close))}")
            raise ValueError(f"Not enough data for STOCH RSI calculations: - {str(len(close))}")

        df_rsi = self.calc_rsi(close, rsi_len)
        rsi = df_rsi["rsi"]

        lowest_low = rsi.rolling(stoch_len, min_periods=stoch_len).min()
        highest_high = rsi.rolling(stoch_len, min_periods=stoch_len).max()

        stoch_rsi = 100 * (rsi - lowest_low) / (highest_high - lowest_low)

        data = {
            "stoch_rsi": stoch_rsi
        }

        df_stoch_rsi = pd.DataFrame(data)

        return df_stoch_rsi


    # Momentum (MOM) bounds filter - to determine if Momentum values in specific range
    # default settings is 13 & 13
    def calc_mom_bounds(self, close: pd.Series, bounds_length: int = 13,
                        quantile_length: int = 987, min_quantile: float = 0.2,
                        max_quantile: float = 0.8) -> pd.DataFrame:
        
        if (len(close) <= bounds_length)  or (len(close) <= quantile_length):
            self._logger.exception(f"Not enough data for mom bounds calculations - {str(len(close))}")
            raise ValueError(f"Not enough data for mom bounds calculations: - {str(len(close))}")

        df_mom = self.calc_roc(close, bounds_length, False)
        mom = df_mom["roc"]
        mom_abs = mom.abs()

        min_val = mom_abs.rolling(quantile_length, min_periods=quantile_length).quantile(min_quantile)
        max_val = mom_abs.rolling(quantile_length, min_periods=quantile_length).quantile(max_quantile)

        data = {
            "mom_ref": mom,
            "mom_abs": mom_abs,
            "mom_min": min_val,
            "mom_max": max_val,
        }

        df_momb = pd.DataFrame(data)

        return df_momb
