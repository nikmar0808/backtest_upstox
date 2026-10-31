"""
NIFTY_S01, NIFTY_S02
entry - close crosses above/below extended first 30m high/low and next candle is pullback
filter - ******Need to implement******
exit - close crosses below/above atr_tsl_long/atr_tsl_short or candle time > exit time or pnl_unrealized < exit_threshold
exit - close crosses below/above atr_tsl_long/atr_tsl_short or candle time > exit time or pnl_unrealized > exit_threshold

NIFTY_S03, NIFTY_S04
entry - close crosses above/below extended first 3m high/low
filter - close greater or less than rma of ema
exit - close crosses below/above atr_tsl_long/atr_tsl_short or candle time > exit time or pnl_unrealized < exit_threshold
exit - close crosses below/above atr_tsl_long/atr_tsl_short or candle time > exit time or pnl_unrealized > exit_threshold

NIFTY_S05, NIFTY_S06
entry - 5,3 GMA of 3m close crosses above/below extended first 3m high/low
filter - close greater or less than rma of ema
exit - close crosses extended below/above first 3m high/low or candle time > exit time or pnl_unrealized < exit_threshold
exit - close crosses below/above atr_tsl_long/atr_tsl_short or candle time > exit time or pnl_unrealized > exit_threshold

NIFTY_S07, NIFTY_S08
entry - close crosses above/below 21 rma of 125 ema of 3m High/Low
filter - close greater or less than 125 ema of 3m HLC3
exit - close crosses extended below/above first 3m high/low or candle time > exit time or pnl_unrealized < exit_threshold
exit - close crosses below/above atr_tsl_long/atr_tsl_short or candle time > exit time or pnl_unrealized > exit_threshold

NIFTY_S09, NIFTY_S10 - smaller SL but longer trade duration exit on Spot
entry - close crosses/near PP ST of 3m HLC3, try making ST ATR parameter a function of main candle ATR
filter - Wick check (to be decided)
exit - close crosses extended below/above first 3m high/low or candle time > exit time or pnl_unrealized < exit_threshold
exit - close crosses below/above atr_tsl_long/atr_tsl_short or candle time > exit time or pnl_unrealized > exit_threshold
"""
STRATEGY_CONFIG_DIR = "datafiles/Strategies"
STRATEGY_FILE_BIN_EXTN = ".bin"
STRATEGY_FILE_DAT_EXTN = ".dat"
STRATEGY_CONFIG_EXCEL_FILE = "StrategyConfig.xlsx"
LOGGER_DIR = "Logs"
nf_strategies = ['NIFTY_S01', 'NIFTY_S02', 'NIFTY_S03', 'NIFTY_S04', 'NIFTY_S05', 'NIFTY_S06', 'NIFTY_S07', 'NIFTY_S08', 'NIFTY_S09', 'NIFTY_S10']
bnf_strategies = ['BANKNIFTY_S01', 'BANKNIFTY_S02', 'BANKNIFTY_S03', 'BANKNIFTY_S04', 'BANKNIFTY_S05', 'BANKNIFTY_S06', 'BANKNIFTY_S07', 'BANKNIFTY_S08', 'BANKNIFTY_S09', 'BANKNIFTY_S10']

strategies = ['NIFTY_S01', 'NIFTY_S02']

STRATEGY_TYPE_INTRADAY = "ID"
STRATEGY_TYPE_OVERNIGHT = "ON"

# Common keys
strategy_id = "strategy_id"
strategy_type = "strategy_type"
multi_leg_strategy = "multi_leg_strategy"
num_of_legs = "num_of_legs"
trade_direction = "trade_direction"
nse_symbol = "nse_symbol"
entry_interval_value = "entry_interval_value"
exit_interval_value = "exit_interval_value"
interval_unit = "interval_unit"
entry_time = "entry_time"
entry_cutoff = "entry_cutoff"
exit_time = "exit_time"
validity_time = "validity_time"
strike_increment = "strike_increment"
buy_strike_offset = "buy_strike_offset"
strike_adjustment_days = "strike_adjustment_days"
strike_offset_days = "strike_offset_days"
strike_adjustment_factor = "strike_adjustment_factor"
strike_max_adjustment_value = "strike_max_adjustment_value"
buy_strike_right = "buy_strike_right"
lot_size = "lot_size"
freeze_quantity = "freeze_quantity"
trade_feed_interval = "trade_feed_interval"
feed_interval_unit = "feed_interval_unit"
trade_feed_interval_exp = "trade_feed_interval_exp"
investment_amount = "investment_amount"
day_loss_limit = "day_loss_limit"
position_loss_limit = "position_loss_limit"
exit_atr_length = "exit_atr_length"
exit_atr_multiplier = "exit_atr_multiplier"
exit_threshold = "exit_threshold"
profit_threshold = "profit_threshold"

# Multileg strategies yet to be defined - N01, N02 strategy keys
sell_st_strike_price = "sell_st_strike_price"
sell_st_strike_expiry = "sell_st_strike_expiry"
sell_st_strike_right = "sell_st_strike_right"

# 3min/30minOR High/Low crosseover/crossunder N01, N02, N03, N04, N05, N06 strategy keys
entry_trigger_HL = "entry_trigger_HL"
entry_trigger_HL_multiplier = "entry_trigger_HL_multiplier"
entry_trigger_HL_high = "entry_trigger_HL_high"
entry_trigger_HL_low = "entry_trigger_HL_low"
entry_filter_rma_ema_length = "entry_filter_rma_ema_length"
entry_trigger_gma_length = "entry_trigger_gma_length"
entry_trigger_gma_ema_length = "entry_trigger_gma_ema_length"
entry_trigger_gma_adaptive = "entry_trigger_gma_adaptive"
entry_trigger_gma_volatility_period = "entry_trigger_gma_volatility_period"
entry_trigger_gma_source = "entry_trigger_gma_source"
entry_filter_ema = "entry_filter_ema"
entry_filter_ema_length = "entry_filter_ema_length"
entry_filter_ema_source = "entry_filter_ema_source"
entry_filter_ema_high = "entry_filter_ema_high"
entry_filter_ema_low = "entry_filter_ema_low"
entry_filter_rma_ema_length = "entry_filter_rma_ema_length"

# 3min OR High/Low crosseover/crossunder N03, N04 strategy keys
"""
entry_trigger_3mHL = "entry_trigger_3mHL"
entry_trigger_3mHL_multiplier = "entry_trigger_3mHL_multiplier"
entry_trigger_3mHL_high = "entry_trigger_3mHL_high"
entry_trigger_3mHL_low = "entry_trigger_3mHL_low"
entry_filter_rma_ema_length = "entry_filter_rma_ema_length"
entry_trigger_gma_length = "entry_trigger_gma_length"
entry_trigger_gma_ema_length = "entry_trigger_gma_ema_length"
entry_trigger_gma_adaptive = "entry_trigger_gma_adaptive"
entry_trigger_gma_volatility_period = "entry_trigger_gma_volatility_period"
entry_trigger_gma_source = "entry_trigger_gma_source"
entry_filter_ema = "entry_filter_ema"
entry_filter_ema_length = "entry_filter_ema_length"
entry_filter_ema_source = "entry_filter_ema_source"
entry_filter_rma_ema_length = "entry_filter_rma_ema_length"
"""

# 30min OR High/Low crosseover/crossunder N05, N06 strategy keys
"""
entry_trigger_30mHL = "entry_trigger_30mHL"
entry_trigger_30mHL_multiplier = "entry_trigger_30mHL_multiplier"
entry_trigger_30mHL_high = "entry_trigger_30mHL_high"
entry_trigger_30mHL_low = "entry_trigger_30mHL_low"
entry_filter_rma_ema_length = "entry_filter_rma_ema_length"
entry_trigger_gma_length = "entry_trigger_gma_length"
entry_trigger_gma_ema_length = "entry_trigger_gma_ema_length"
entry_trigger_gma_adaptive = "entry_trigger_gma_adaptive"
entry_trigger_gma_volatility_period = "entry_trigger_gma_volatility_period"
entry_trigger_gma_source = "entry_trigger_gma_source"
entry_filter_ema = "entry_filter_ema"
entry_filter_ema_length = "entry_filter_ema_length"
entry_filter_ema_source = "entry_filter_ema_source"
entry_filter_rma_ema_length = "entry_filter_rma_ema_length"
"""

# EMA crosseover/crossunder N07, N08 strategy keys
entry_trigger_ema_length = "entry_trigger_ema_length"
entry_trigger_ema_source = "entry_trigger_ema_source"
entry_trigger_rma_ema_length = "entry_trigger_rma_ema_length"
entry_filter_ema = "entry_filter_ema"
entry_filter_ema_length = "entry_filter_ema_length"
entry_filter_ema_source = "entry_filter_ema_source"

# SUPERTREND crosseover/crossunder N09, N10 strategy keys
entry_trigger_st_atr_length = "entry_trigger_st_atr_length"
entry_trigger_st_atr_factor = "entry_trigger_st_atr_factor"
entry_filter_ema = "entry_filter_ema"
entry_filter_ema_length = "entry_filter_ema_length"
entry_filter_ema_source = "entry_filter_ema_source"
entry_filter_rma_ema_length = "entry_filter_rma_ema_length"