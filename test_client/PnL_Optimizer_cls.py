import sys, os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from backtest_common import __backtestconfig__
trade_data_details_dir = __backtestconfig__.TRADE_DATA_DETAILS_DIR
trade_data_file_dir = __backtestconfig__.TRADE_DATA_FILE_DIR
backtest_reports_dir = __backtestconfig__.BACKTEST_REPORTS_DIR

#@profile
def main():

    # # NIFTY S01/S02 Trade Research Lab

    # ## Dataset Understanding

    # You provided:

    # * S01 = Long-side strategy (buying ITM Calls)
    # * S02 = Short-side strategy (buying ITM Puts)
    # * Entry:

    # * 3-minute spot candle closes above first 3-minute candle high → Long
    # * 3-minute spot candle closes below first 3-minute candle low → Short
    # * Exit:

    # * Pure time-based exit at 3:12 PM

    # This is extremely valuable because:

    # * Entries are isolated cleanly.
    # * No stop-loss distortion.
    # * No trailing stop distortion.
    # * No discretionary exits.

    # This means we can study:

    # 1. Raw signal edge
    # 2. MAE recovery behavior
    # 3. Optimal stop thresholds
    # 4. Profit capture efficiency
    # 5. Efficient exit architecture
    # 6. Whether trades deserve wider/tighter stops
    # 7. Whether time exits are suboptimal

    # ---

    # # Initial High-Level Insights From Your Uploaded Data

    # ## 1. Your Entries ARE NOT Random

    # There are many very large winners.

    # This strongly suggests:

    # * breakout continuation exists,
    # * directional edge exists,
    # * entry logic has predictive value.

    # The system is NOT dead.

    # ---

    # ## 2. Some Winning Trades Require Massive Pain

    # Examples exist where:

    # * trade eventually finishes profitable,
    # * but first suffers extremely deep unrealized loss.

    # This is dangerous because:

    # * large stops destroy risk-adjusted returns,
    # * but tight stops may kill eventual winners.

    # This is exactly why MAE percentile analysis matters.

    # ---

    # ## 3. S01 Long Side Appears More Fragile

    # The long-side call-buying strategy experiences:

    # * larger negative excursions,
    # * more violent decay,
    # * larger left-on-table swings.

    # Likely causes:

    # * option premium decay,
    # * intraday reversals,
    # * gap behavior,
    # * long-side volatility compression.

    # ---

    # ## 4. S02 Put-Buying Side Appears Cleaner

    # Short-side momentum appears:

    # * faster,
    # * cleaner,
    # * less noisy.

    # This is common in index systems because downside moves tend to be:

    # * sharper,
    # * more impulsive,
    # * volatility expanding.

    # ---

    # ## 5. Time Exit at 3:12 PM Is Probably NOT Optimal

    # Very likely:

    # * many profitable trades peak much earlier,
    # * many losing trades never recover,
    # * theta decay/chop hurts late-session holding.

    # This is where duration analysis becomes critical.

    # ---

    # # What We Want To Discover

    # The code below will answer:

    # ## Question 1

    # Among trades that eventually became profitable:

    # > How much drawdown did they usually require before recovery?

    # This helps determine:

    # * optimal SL width,
    # * whether current future stop is too tight.

    # ---

    # ## Question 2

    # Among trades that NEVER recovered:

    # > At what loss threshold should they ideally have been exited?

    # This helps determine:

    # * optimal loss cutoff.

    # ---

    # ## Question 3

    # > What stop threshold maximizes expectancy?

    # This is one of the most important professional system metrics.

    # ---

    # ## Question 4

    # > Do good trades move quickly?

    # If yes:

    # * time-decay exits become powerful.

    # ---

    # ## Question 5

    # > Is time exit inferior to dynamic exits?

    # We estimate:

    # * trailing logic,
    # * breakeven logic,
    # * partial exits.

    # ---

    # FULL RESEARCH LAB CODE

    # ============================================================
    # LOAD DATA
    # ============================================================
    # ============================================================
    # LOAD CSV
    # ============================================================

    S01_PATH = f"{trade_data_file_dir}NIFTY_S01_Signal_Trade_File.csv"
    S02_PATH = f"{trade_data_file_dir}NIFTY_S02_Signal_Trade_File.csv"

    S01 = pd.read_csv(S01_PATH)
    S02 = pd.read_csv(S02_PATH)

    S01["strategy"] = "S01_LONG_CALL"
    S02["strategy"] = "S02_LONG_PUT"

    # combine

    df = pd.concat([S01, S02], ignore_index=True)

    # ============================================================
    # CLEANING
    # ============================================================

    numeric_cols = [
        "overall_pnl",
        "pnl_realized",
        "slippage",
        "net_pnl_after_slippage",
        "profit_left_on_the_table",
        "max_unrealized_profit_during_trade",
        "max_unrealized_loss_during_trade"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # aliases

    df["final_pnl"] = df["net_pnl_after_slippage"]

    df["mae"] = abs(df["max_unrealized_loss_during_trade"])

    df["mfe"] = df["max_unrealized_profit_during_trade"]

    # duration

    df["buy_datetime"] = pd.to_datetime(df["buy_datetime"])
    df["sell_datetime"] = pd.to_datetime(df["sell_datetime"])

    df["trade_duration_minutes"] = (
        df["sell_datetime"] - df["buy_datetime"]
    ).dt.total_seconds() / 60

    # ============================================================
    # BASIC STATS
    # ============================================================

    print("\n================ BASIC STATS ================\n")

    print(df.groupby("strategy")["final_pnl"].agg([
        "count",
        "sum",
        "mean",
        "median"
    ]))

    # ============================================================
    # WINNERS / LOSERS
    # ============================================================

    winners = df[df["final_pnl"] > 0].copy()
    losers = df[df["final_pnl"] <= 0].copy()

    print("\n================ WIN RATE ================\n")

    win_rate = len(winners) / len(df)

    print(f"Overall Win Rate: {win_rate:.2%}")

    # ============================================================
    # CAPTURE RATIO
    # ============================================================

    # How efficiently did we monetize available opportunity?

    df["capture_ratio"] = np.where(
        df["mfe"] > 0,
        df["final_pnl"] / df["mfe"],
        np.nan
    )

    print("\n================ CAPTURE RATIO ================\n")

    print(df["capture_ratio"].describe())

    # ============================================================
    # PAIN RATIO
    # ============================================================

    # How much pain required for profit?

    df["pain_ratio"] = np.where(
        df["final_pnl"] > 0,
        df["mae"] / df["final_pnl"],
        np.nan
    )

    print("\n================ PAIN RATIO ================\n")

    print(df["pain_ratio"].describe())

    # ============================================================
    # WINNER MAE PERCENTILES
    # ============================================================

    print("\n================ WINNER MAE PERCENTILES ================\n")

    winner_mae = winners["mae"]

    percentiles = [50, 60, 70, 80, 90, 95, 99]

    for p in percentiles:

        val = np.percentile(winner_mae, p)

        print(f"{p}th percentile winner MAE: {val:.2f}")

    # ============================================================
    # INTERPRETATION
    # ============================================================

    p80 = np.percentile(winner_mae, 80)
    p90 = np.percentile(winner_mae, 90)

    print("\nINTERPRETATION")
    print(f"80% of winners survive within MAE = {p80:.2f}")
    print(f"90% of winners survive within MAE = {p90:.2f}")

    # ============================================================
    # RECOVERY PROBABILITY CURVE
    # ============================================================

    print("\n================ RECOVERY PROBABILITY ================\n")

    thresholds = np.arange(500, 30000, 500)

    recovery_results = []

    for t in thresholds:

        subset = df[df["mae"] >= t]

        if len(subset) == 0:
            continue

        recovered = subset[subset["final_pnl"] > 0]

        recovery_rate = len(recovered) / len(subset)

        avg_final = subset["final_pnl"].mean()

        recovery_results.append({
            "threshold": t,
            "trade_count": len(subset),
            "recovery_rate": recovery_rate,
            "avg_final_pnl": avg_final
        })

    recovery_df = pd.DataFrame(recovery_results)

    print(recovery_df)

    # ============================================================
    # OPTIMAL STOP THRESHOLD ANALYSIS
    # ============================================================

    print("\n================ STOP THRESHOLD ANALYSIS ================\n")

    stop_results = []

    for stop in thresholds:

        simulated_pnl = []

        for _, row in df.iterrows():

            # stopped out before time exit
            if row["mae"] >= stop:

                pnl = -stop

            else:

                pnl = row["final_pnl"]

            simulated_pnl.append(pnl)

        simulated_pnl = np.array(simulated_pnl)

        gross_profit = simulated_pnl[simulated_pnl > 0].sum()

        gross_loss = abs(
            simulated_pnl[simulated_pnl < 0].sum()
        )

        profit_factor = (
            gross_profit / gross_loss
            if gross_loss != 0
            else np.nan
        )

        expectancy = simulated_pnl.mean()

        stop_results.append({
            "stop_threshold": stop,
            "total_pnl": simulated_pnl.sum(),
            "avg_trade": expectancy,
            "win_rate": (simulated_pnl > 0).mean(),
            "profit_factor": profit_factor,
            "max_loss": simulated_pnl.min()
        })

    stop_df = pd.DataFrame(stop_results)

    print(
        stop_df.sort_values(
            by="profit_factor",
            ascending=False
        ).head(20)
    )

    # ============================================================
    # SURVIVAL ANALYSIS
    # ============================================================

    print("\n================ WINNER SURVIVAL ================\n")

    survival_results = []

    for stop in thresholds:

        surviving_winners = winners[
            winners["mae"] <= stop
        ]

        survival_rate = (
            len(surviving_winners) / len(winners)
        )

        survival_results.append({
            "stop_threshold": stop,
            "winner_survival_rate": survival_rate
        })

    survival_df = pd.DataFrame(survival_results)

    print(survival_df)

    # ============================================================
    # TRADES THAT NEVER RECOVERED
    # ============================================================

    print("\n================ NON-RECOVERING TRADES ================\n")

    never_recovered = losers.copy()

    print(never_recovered[[
        "strategy",
        "trade_date",
        "final_pnl",
        "mae",
        "mfe"
    ]].head(20))

    # ============================================================
    # ESTIMATE BEST LOSS CUT-OFF
    # ============================================================

    print("\n================ BEST LOSS CUT-OFF ================\n")

    loss_cutoff_results = []

    for stop in thresholds:

        losing_subset = losers.copy()

        adjusted_losses = np.where(
            losing_subset["mae"] >= stop,
            -stop,
            losing_subset["final_pnl"]
        )

        avg_loss = adjusted_losses.mean()

        total_loss = adjusted_losses.sum()

        loss_cutoff_results.append({
            "stop_threshold": stop,
            "avg_loss": avg_loss,
            "total_loss": total_loss
        })

    loss_cutoff_df = pd.DataFrame(loss_cutoff_results)

    print(
        loss_cutoff_df.sort_values(
            by="total_loss",
            ascending=False
        ).head(20)
    )

    # ============================================================
    # TRADE DURATION ANALYSIS
    # ============================================================

    print("\n================ TRADE DURATION ANALYSIS ================\n")

    bins = [0, 15, 30, 60, 120, 240, 500]

    summary = df.groupby(
        pd.cut(df["trade_duration_minutes"], bins=bins)
    )["final_pnl"].agg([
        "count",
        "mean",
        "sum"
    ])

    print(summary)

    # ============================================================
    # PLOTS
    # ============================================================

    # ------------------------------------------------------------
    # Recovery Probability Curve
    # ------------------------------------------------------------

    plt.figure(figsize=(12, 6))

    plt.plot(
        recovery_df["threshold"],
        recovery_df["recovery_rate"]
    )

    plt.title("Recovery Probability vs MAE")
    plt.xlabel("MAE Threshold")
    plt.ylabel("Recovery Probability")
    plt.grid(True)

    # ------------------------------------------------------------
    # Profit Factor vs Stop
    # ------------------------------------------------------------

    plt.figure(figsize=(12, 6))

    plt.plot(
        stop_df["stop_threshold"],
        stop_df["profit_factor"]
    )

    plt.title("Profit Factor vs Stop Threshold")
    plt.xlabel("Stop Threshold")
    plt.ylabel("Profit Factor")
    plt.grid(True)

    # ------------------------------------------------------------
    # Total PnL vs Stop
    # ------------------------------------------------------------

    plt.figure(figsize=(12, 6))

    plt.plot(
        stop_df["stop_threshold"],
        stop_df["total_pnl"]
    )

    plt.title("Total PnL vs Stop Threshold")
    plt.xlabel("Stop Threshold")
    plt.ylabel("Total PnL")
    plt.grid(True)

    # ------------------------------------------------------------
    # MAE vs Final PnL
    # ------------------------------------------------------------

    plt.figure(figsize=(12, 6))

    plt.scatter(
        df["mae"],
        df["final_pnl"],
        alpha=0.6
    )

    plt.axhline(0, linestyle="--")

    plt.title("MAE vs Final PnL")
    plt.xlabel("MAE")
    plt.ylabel("Final PnL")
    plt.grid(True)

    # ------------------------------------------------------------
    # Capture Ratio Distribution
    # ------------------------------------------------------------

    plt.figure(figsize=(12, 6))

    plt.hist(
        df["capture_ratio"].dropna(),
        bins=40
    )

    plt.title("Capture Ratio Distribution")
    plt.xlabel("Capture Ratio")
    plt.ylabel("Frequency")
    plt.grid(True)

    plt.show()

    # ============================================================
    # SAVE OUTPUTS
    # ============================================================

    recovery_df.to_csv(
        "recovery_probability_analysis.csv",
        index=False
    )

    stop_df.to_csv(
        "stop_threshold_analysis.csv",
        index=False
    )

    survival_df.to_csv(
        "winner_survival_analysis.csv",
        index=False
    )

    loss_cutoff_df.to_csv(
        "loss_cutoff_analysis.csv",
        index=False
    )

    print("\nAnalysis complete.")
    print("CSV reports exported.")

if __name__ == '__main__':
    main()
