import sys, os, re
from backtest_common import __backtestconfig__
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#import caas_jupyter_tools
from matplotlib import dates as mdates
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import glob


# Create and configure logger
report_generator_logger = logging.getLogger("logs/report_generator.log")
report_generator_logger.addHandler(logging.FileHandler("logs/report_generator.log", mode='a'))
report_generator_logger.setLevel(logging.INFO)

class ReportGenerator:

    def __init__(self,broker,logger=report_generator_logger):
        self.broker=broker
        self.logger=logger
        self.trade_data_details_dir = __backtestconfig__.TRADE_DATA_DETAILS_DIR
        self.trade_data_file_dir = __backtestconfig__.TRADE_DATA_FILE_DIR
        self.backtest_reports_dir = __backtestconfig__.BACKTEST_REPORTS_DIR

    def generate_signal_level_reports(self, strategy_id):

        # Creating an Excel workbook dashboard from the signal trade file generated for this strategy.
        # This code will:
        # - read the CSV
        # - compute core metrics (using pnl_realized as requested)
        # - produce summary tables and charts
        # - save an Excel workbook with multiple sheets and embed key charts as images
        # - display a few key tables inside the notebook for quick inspection
        #
        # Output files:
        # - self.backtest_reports_dir/{strategy_id}_trade_dashboard_final.xlsx
        # - several PNG charts saved under self.backtest_reports_dir
        #strategy_id = strategy_obj.strategy_id
        # Signal Trade File path
        signal_trade_file_name = f"{strategy_id}_Signal_Trade_File.csv"
        signal_trade_file = os.path.join(self.trade_data_file_dir, signal_trade_file_name)
        df = pd.read_csv(signal_trade_file)
        df.columns = [c.strip() for c in df.columns]

        # Ensure required columns exist
        required = ["trade_id","trade_date","buy_datetime","sell_datetime","investment_amount","instrument_key","trading_symbol","lot_size","num_of_lots","overall_pnl","pnl_realized","slippage","max_unrealized_profit_during_trade","max_unrealized_loss_during_trade"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing expected columns in uploaded file: {missing}")

        # Parse datetimes
        df["buy_datetime"] = pd.to_datetime(df["buy_datetime"], errors="coerce")
        df["sell_datetime"] = pd.to_datetime(df["sell_datetime"], errors="coerce")
        df["trade_date"] = pd.to_datetime(df["trade_date"], errors="coerce").dt.date

        # Numeric parsing for key numeric columns
        numcols = ["investment_amount","lot_size","num_of_lots","overall_pnl","pnl_realized","slippage","max_unrealized_profit_during_trade","max_unrealized_loss_during_trade"]
        for c in numcols:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        # Derived fields
        df["duration_min"] = (df["sell_datetime"] - df["buy_datetime"]).dt.total_seconds() / 60.0
        df["return_pct"] = df["pnl_realized"] / df["investment_amount"] * 100.0
        df["win"] = (df["pnl_realized"] > 0).astype(int)
        df["loss"] = (df["pnl_realized"] < 0).astype(int)
        df["flat"] = (df["pnl_realized"] == 0).astype(int)

        # Core metrics
        total_trades = len(df)
        wins = int(df["win"].sum()); losses = int(df["loss"].sum()); flats = int(df["flat"].sum())
        #net_pnl = float(df["pnl_realized"].sum(skipna=True))
        net_pnl = float((df["pnl_realized"] - df["slippage"]).sum(skipna=True))
        gross_profit = float(df.loc[df["pnl_realized"]>0, "pnl_realized"].sum())
        gross_loss = float(df.loc[df["pnl_realized"]<0, "pnl_realized"].sum())
        win_rate = wins/total_trades*100 if total_trades>0 else np.nan
        avg_win = float(df.loc[df["pnl_realized"]>0, "pnl_realized"].mean()) if wins>0 else np.nan
        avg_loss = float(df.loc[df["pnl_realized"]<0, "pnl_realized"].mean()) if losses>0 else np.nan
        profit_factor = gross_profit/abs(gross_loss) if gross_loss!=0 else np.inf
        avg_trade = net_pnl/total_trades if total_trades>0 else np.nan

        # Equity, drawdown
        equity = df["pnl_realized"].fillna(0).cumsum().rename("Equity")
        cummax = equity.cummax()
        drawdown = equity - cummax
        max_drawdown = float(drawdown.min()) if len(drawdown)>0 else 0.0

        # Find the maximum count of trades in a single day
        # Group by 'trade_date' and count the number of trades (rows)
        trades_per_day = df.groupby('trade_date').size()
        
        max_trades = trades_per_day.max()

        # Expectancy
        expectancy = (win_rate/100.0)*(0 if np.isnan(avg_win) else avg_win) + (1-win_rate/100.0)*(0 if np.isnan(avg_loss) else avg_loss)

        # By-day
        by_day = df.groupby("trade_date", observed=True)["pnl_realized"].sum().reset_index().rename(columns={"pnl_realized":"DailyPnL"})

        # By-month
        by_month = df.groupby(pd.to_datetime(df['trade_date'], errors='coerce').dt.to_period("M"), observed=True)["pnl_realized"].sum().reset_index().rename(columns={"pnl_realized":"MonthlyPnL"})

        # By instrument
        #by_instrument = df.groupby("instrument_key", observed=True)["pnl_realized"].agg(["count","sum","mean","std"]).reset_index().rename(columns={"count":"Trades","sum":"TotalPnL","mean":"AvgPnL","std":"StdPnL"}).sort_values("TotalPnL", ascending=False)
        #by_instrument["PctOfTotal"] = by_instrument["TotalPnL"] / by_instrument["TotalPnL"].sum() * 100.0

        # Holding time buckets
        bins = [-1, 1, 60, 60*24, 60*24*7, np.inf]  # minutes: <1min, 1-60, 1-24h, 1-7d, >7d
        labels = ["<1min","1-60min","1-24h","1-7d",">7d"]
        df["holding_bucket"] = pd.cut(df["duration_min"].fillna(-1), bins=bins, labels=labels)
        holding_summary = df.groupby("holding_bucket", observed=True)["pnl_realized"].agg(["count","sum","mean"]).reset_index().rename(columns={"count":"Trades","sum":"TotalPnL","mean":"AvgPnL"})

        # Slippage impact (slippage as absolute and as % of realized pnl)
        df["slippage_abs"] = df["slippage"].abs()
        df["slippage_pct_of_pnl"] = np.where(df["pnl_realized"]!=0, df["slippage_abs"] / df["pnl_realized"] * 100.0, np.nan)
        slippage_summary = pd.DataFrame({
            "TotalSlippage": [df["slippage"].sum(skipna=True)],
            "AvgSlippage": [df["slippage"].mean(skipna=True)],
            "MedianSlippage": [df["slippage"].median(skipna=True)],
            "PctTradesWithSlippage": [ (df["slippage"].abs()>0).sum() / total_trades * 100.0 ]
        })

        # Unrealized excursions summary
        unrealized_summary = pd.DataFrame({
            "AvgMaxUnrealizedProfit": [df["max_unrealized_profit_during_trade"].mean(skipna=True)],
            "AvgMaxUnrealizedLoss": [df["max_unrealized_loss_during_trade"].mean(skipna=True)],
            "MedianMaxUnrealizedProfit": [df["max_unrealized_profit_during_trade"].median(skipna=True)],
            "MedianMaxUnrealizedLoss": [df["max_unrealized_loss_during_trade"].median(skipna=True)]
        })

        # Streaks (trade-ordered by buy_datetime)
        df_sorted = df.sort_values("buy_datetime").reset_index(drop=True)
        streaks = []
        cur_type = None; cur_len = 0; cur_pnl = 0.0
        for _, r in df_sorted.iterrows():
            kind = "win" if r["pnl_realized"]>0 else ("loss" if r["pnl_realized"]<0 else "flat")
            if cur_type is None:
                cur_type=kind; cur_len=1; cur_pnl=r["pnl_realized"]
            elif kind==cur_type:
                cur_len+=1; cur_pnl+=r["pnl_realized"]
            else:
                streaks.append({"type":cur_type,"length":cur_len,"pnl":cur_pnl})
                cur_type=kind; cur_len=1; cur_pnl=r["pnl_realized"]
        streaks.append({"type":cur_type,"length":cur_len,"pnl":cur_pnl})
        streaks_df = pd.DataFrame(streaks)

        # Top and worst trades
        top_trades = df.sort_values("pnl_realized", ascending=False).head(20)
        worst_trades = df.sort_values("pnl_realized").head(20)

        # Prepare metrics table for Excel
        metrics_table = pd.DataFrame({
            "Metric":[
                "Total Trades","Wins","Losses","Flats","Win Rate %",
                "Net PnL","Gross Profit","Gross Loss","Profit Factor",
                "Average Trade PnL","Average Win","Average Loss","Max Drawdown","Max Trades per Day", "Expectancy"
            ],
            "Value":[
                total_trades, wins, losses, flats, round(win_rate,4),
                round(net_pnl,2), round(gross_profit,2), round(gross_loss,2),
                round(profit_factor,2) if np.isfinite(profit_factor) else "∞",
                round(avg_trade,2), round(avg_win,2) if not np.isnan(avg_win) else np.nan,
                round(avg_loss,2) if not np.isnan(avg_loss) else np.nan, round(max_drawdown,2), max_trades, round(expectancy,2)
            ]
        })

        # Create charts (matplotlib) and save as PNGs
        os.makedirs(f"{self.backtest_reports_dir}dashboard_figs", exist_ok=True)

        # Equity curve
        plt.figure(figsize=(10,4))
        equity.plot()
        plt.title("Equity Curve (Cumulative PnL)")
        plt.xlabel("Trade Index")
        plt.ylabel("Cumulative PnL")
        plt.tight_layout()
        plt.savefig(f"{self.backtest_reports_dir}dashboard_figs/{strategy_id}_equity_curve.png")
        plt.close()

        # Daily PnL bar
        plt.figure(figsize=(10,4))
        plt.bar(by_day["trade_date"].astype(str), by_day["DailyPnL"])
        plt.title("Daily PnL")
        plt.xlabel("Date")
        plt.ylabel("Daily PnL")
        plt.xticks(rotation=90)
        plt.tight_layout()
        plt.savefig(f"{self.backtest_reports_dir}dashboard_figs/{strategy_id}_daily_pnl.png")
        plt.close()

        # Monthly PnL bar
        plt.figure(figsize=(10,4))
        plt.bar(by_month["trade_date"].astype(str), by_month["MonthlyPnL"])
        plt.title("Monthly PnL")
        plt.xlabel("Date")
        plt.ylabel("Monthly PnL")
        plt.xticks(rotation=90)
        plt.tight_layout()
        plt.savefig(f"{self.backtest_reports_dir}dashboard_figs/{strategy_id}_monthly_pnl.png")
        plt.close()
        """
        # By instrument top 15
        plt.figure(figsize=(10,4))
        top_instr = by_instrument.head(15)
        plt.bar(top_instr["instrument_key"].astype(str), top_instr["TotalPnL"])
        plt.title("Top 15 Instruments by Total PnL")
        plt.xlabel("Instrument")
        plt.ylabel("Total PnL")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(f"{self.backtest_reports_dir}dashboard_figs/{strategy_id}_top_instruments.png")
        plt.close()
        """

        # Holding time histogram
        plt.figure(figsize=(8,3))
        plt.hist(df["duration_min"].dropna(), bins=40)
        plt.title("Holding Time (minutes) Distribution")
        plt.xlabel("Duration (min)")
        plt.ylabel("Count")
        plt.tight_layout()
        plt.savefig(f"{self.backtest_reports_dir}dashboard_figs/{strategy_id}_holding_time_hist.png")
        plt.close()

        # Duration vs PnL scatter (sample)
        sample = df.dropna(subset=["duration_min","pnl_realized"])
        if len(sample) > 2000: sample = sample.sample(2000, random_state=1)
        plt.figure(figsize=(6,4))
        plt.scatter(sample["duration_min"], sample["pnl_realized"], s=6)
        plt.title("Duration vs PnL (sample)")
        plt.xlabel("Duration (min)")
        plt.ylabel("PnL (realized)")
        plt.tight_layout()
        plt.savefig(f"{self.backtest_reports_dir}dashboard_figs/{strategy_id}_duration_vs_pnl.png")
        plt.close()

        # Drawdown chart
        plt.figure(figsize=(10,4))
        plt.plot(equity.index, equity.values)
        plt.plot(cummax.index, cummax.values)
        plt.fill_between(range(len(drawdown)), drawdown.values, 0)
        plt.title("Equity and Drawdowns")
        plt.xlabel("Trade Index")
        plt.ylabel("Value")
        plt.tight_layout()
        plt.savefig(f"{self.backtest_reports_dir}dashboard_figs/{strategy_id}_drawdown.png")
        plt.close()

        # Save everything to Excel with sheets; embed charts
        #out_excel = f"{self.backtest_reports_dir}trade_dashboard_final.xlsx"
        out_excel_filename = f"{strategy_id}_trade_dashboard_final.xlsx"
        out_excel = os.path.join(self.backtest_reports_dir, out_excel_filename)

        with pd.ExcelWriter(out_excel, engine="xlsxwriter") as writer:
            metrics_table.to_excel(writer, sheet_name="Metrics", index=False)
            df.to_excel(writer, sheet_name="AggregatedTrades", index=False)
            by_day.to_excel(writer, sheet_name="DailyPnL", index=False)
            by_month.to_excel(writer, sheet_name="MonthlyPnL", index=False)
            #by_instrument.to_excel(writer, sheet_name="ByInstrument", index=False)
            holding_summary.to_excel(writer, sheet_name="HoldingBuckets", index=False)
            slippage_summary.to_excel(writer, sheet_name="SlippageSummary", index=False)
            unrealized_summary.to_excel(writer, sheet_name="UnrealizedSummary", index=False)
            streaks_df.to_excel(writer, sheet_name="Streaks", index=False)
            top_trades.to_excel(writer, sheet_name="TopTrades", index=False)
            worst_trades.to_excel(writer, sheet_name="WorstTrades", index=False)
            
            # Insert images into a Dashboard sheet
            workbook  = writer.book
            worksheet = workbook.add_worksheet("Charts")
            writer.sheets["Charts"] = worksheet
            # place images gap of 24 rows
            worksheet.insert_image("B2", f"{self.backtest_reports_dir}dashboard_figs/{strategy_id}_equity_curve.png")
            worksheet.insert_image("B26", f"{self.backtest_reports_dir}dashboard_figs/{strategy_id}_daily_pnl.png")
            worksheet.insert_image("B50", f"{self.backtest_reports_dir}dashboard_figs/{strategy_id}_monthly_pnl.png")
            #worksheet.insert_image("B50", f"{self.backtest_reports_dir}dashboard_figs/{strategy_id}_top_instruments.png")
            worksheet.insert_image("B74", f"{self.backtest_reports_dir}dashboard_figs/{strategy_id}_holding_time_hist.png")
            worksheet.insert_image("B98", f"{self.backtest_reports_dir}dashboard_figs/{strategy_id}_duration_vs_pnl.png")
            worksheet.insert_image("B122", f"{self.backtest_reports_dir}dashboard_figs/{strategy_id}_drawdown.png")

        # Display a few key tables for immediate inspection
        #caas_jupyter_tools.display_dataframe_to_user("Metrics Summary", metrics_table)
        #caas_jupyter_tools.display_dataframe_to_user("By Instrument (top 15)", by_instrument.head(15))
        #caas_jupyter_tools.display_dataframe_to_user("Holding Buckets Summary", holding_summary)
        #caas_jupyter_tools.display_dataframe_to_user("Slippage Summary", slippage_summary)
        #caas_jupyter_tools.display_dataframe_to_user("Unrealized Summary", unrealized_summary)

        print("Saved Excel workbook to:", out_excel)

    def generate_aggregate_pnl_reports(self):

        """
        Aggregate multiple strategy dashboard workbooks and produce:
        - aggregated Excel workbook (ByDay, ByMonth, per-strategy sheets)
        - a report-style PDF (cover, charts, per-strategy equity pages, summary table)

        Place this script in the folder that contains files named like:
        <strategy_id>_trade_dashboard_final.xlsx

        Outputs (saved to /datafiles/Reports):
        - aggregated_pnl_with_charts.xlsx
        - aggregated_pnl_report.pdf

        Dependencies: pandas, matplotlib, xlsxwriter, reportlab, glob, os
        """
        DATA_FOLDER = f"{self.backtest_reports_dir}"
        EXCEL_GLOB = os.path.join(DATA_FOLDER, "*_trade_dashboard_final.xlsx")
        OUT_XLSX = os.path.join(DATA_FOLDER, "aggregated_pnl_with_charts.xlsx")
        OUT_PDF = os.path.join(DATA_FOLDER, "aggregated_pnl_report.pdf")
        CHART_DIR = os.path.join(DATA_FOLDER, "dashboard_figs")
        os.makedirs(CHART_DIR, exist_ok=True)

        # Automatically scan folder for all *_trade_dashboard_final.xlsx files

        #!/usr/bin/env python3

        # ----- Discover files -----
        files = glob.glob(EXCEL_GLOB)
        if not files:
            raise FileNotFoundError(f"No files matching {EXCEL_GLOB} found")

        # ----- Read DailyPnL sheets -----
        dfs = {}
        for f in sorted(files):
            base = os.path.basename(f)
            strategy_id = base.split("_trade_dashboard_final.xlsx")[0]
            df = pd.read_excel(f, sheet_name="DailyPnL")
            # Normalize column names
            df.columns = [c.strip() for c in df.columns]
            if "trade_date" not in df.columns or "DailyPnL" not in df.columns:
                raise ValueError(f"File {f} must contain sheet 'DailyPnL' with columns trade_date and DailyPnL")
            df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
            dfs[strategy_id] = df.set_index("trade_date")

        # ----- Merge per-day data -----
        all_daily = pd.concat(dfs.values(), axis=1, keys=dfs.keys())
        all_daily.columns = [f"{s}_{col}" for s, col in all_daily.columns]
        # find PnL columns
        pnl_cols = [c for c in all_daily.columns if c.endswith("DailyPnL")]
        all_daily["TotalPnL"] = all_daily[pnl_cols].sum(axis=1)
        by_day = all_daily.reset_index().rename(columns={"trade_date": "TradeDate"})
        by_day = by_day.sort_values("TradeDate").reset_index(drop=True)
        by_day["Month"] = pd.to_datetime(by_day["TradeDate"]).dt.to_period("M")

        # ----- By month aggregation -----
        by_month = by_day.groupby("Month")[ ["TotalPnL"] + pnl_cols ].sum().reset_index()
        by_month["Month"] = by_month["Month"].astype(str)
        by_month = by_month.sort_values("Month").reset_index(drop=True)

        # Per-strategy ByMonth
        by_month_per_strategy = {}
        for sid in dfs.keys():
            col = f"{sid}_DailyPnL"
            dfm = by_day.groupby("Month")[[col]].sum().reset_index()
            dfm["Month"] = dfm["Month"].astype(str)
            by_month_per_strategy[sid] = dfm

        # ----- Save Excel workbook -----
        with pd.ExcelWriter(OUT_XLSX, engine="xlsxwriter") as writer:
            by_day.to_excel(writer, sheet_name="ByDay", index=False)
            by_month.to_excel(writer, sheet_name="ByMonth", index=False)
            for sid, df in dfs.items():
                df.reset_index().to_excel(writer, sheet_name=f"{sid}_DailyPnL", index=False)
            for sid, dfm in by_month_per_strategy.items():
                dfm.to_excel(writer, sheet_name=f"{sid}_ByMonth", index=False)

            workbook = writer.book
            # Freeze headers
            writer.sheets["ByDay"].freeze_panes(1, 0)
            writer.sheets["ByMonth"].freeze_panes(1, 0)

            # Date format and auto column widths
            date_fmt = workbook.add_format({"num_format": "yyyy-mm-dd"})
            for sheet_name, worksheet in writer.sheets.items():
                if sheet_name == "ByDay":
                    df_example = by_day
                elif sheet_name == "ByMonth":
                    df_example = by_month
                elif sheet_name.endswith("_DailyPnL"):
                    sid = sheet_name.replace("_DailyPnL", "")
                    df_example = dfs[sid].reset_index()
                elif sheet_name.endswith("_ByMonth"):
                    sid = sheet_name.replace("_ByMonth", "")
                    df_example = by_month_per_strategy[sid]
                else:
                    df_example = None
                if df_example is not None:
                    for idx, col in enumerate(df_example.columns):
                        col_width = max(len(str(col)), df_example[col].astype(str).str.len().max()) + 2
                        if "date" in col.lower() or "Date" in col:
                            worksheet.set_column(idx, idx, col_width, date_fmt)
                        else:
                            worksheet.set_column(idx, idx, col_width)

            # Conditional formatting for PnL columns
            pos_fmt = workbook.add_format({"font_color": "green"})
            neg_fmt = workbook.add_format({"font_color": "red"})
            for sheet_name in list(writer.sheets.keys()):
                if sheet_name in ["ByDay", "ByMonth"] or sheet_name.endswith("_ByMonth"):
                    ws = writer.sheets[sheet_name]
                    if sheet_name == "ByDay":
                        df_example = by_day
                    elif sheet_name == "ByMonth":
                        df_example = by_month
                    else:
                        sid = sheet_name.replace("_ByMonth", "")
                        df_example = by_month_per_strategy[sid]
                    for idx, col in enumerate(df_example.columns):
                        if "PnL" in col:
                            ws.conditional_format(1, idx, len(df_example), idx, {"type": "cell", "criteria": ">=", "value": 0, "format": pos_fmt})
                            ws.conditional_format(1, idx, len(df_example), idx, {"type": "cell", "criteria": "<", "value": 0, "format": neg_fmt})

            # Create charts as PNGs
            # Chart 1: Total PnL by Month
            fig1_path = os.path.join(CHART_DIR, "monthly_pnl.png")
            plt.figure(figsize=(10,4))
            plt.bar(by_month["Month"], by_month["TotalPnL"])
            plt.xticks(rotation=45)
            plt.title("Total PnL by Month")
            plt.tight_layout()
            plt.savefig(fig1_path)
            plt.close()

            # Chart 2: Equity curve (all strategies + total)
            fig2_path = os.path.join(CHART_DIR, "equity_curve.png")
            plt.figure(figsize=(11,5))
            for sid in dfs.keys():
                col = f"{sid}_DailyPnL"
                if col in by_day:
                    plt.plot(by_day["TradeDate"], by_day[col].cumsum(), label=sid)
            plt.plot(by_day["TradeDate"], by_day["TotalPnL"].cumsum(), label="Total", linewidth=2)
            plt.legend()
            plt.xticks(rotation=45)
            plt.title("Equity Curve (Cumulative PnL)")
            plt.tight_layout()
            plt.savefig(fig2_path)
            plt.close()

            # Chart 3: Stacked monthly PnL by strategy
            fig3_path = os.path.join(CHART_DIR, "monthly_pnl_stacked.png")
            plt.figure(figsize=(11,6))
            strategy_cols = [c for c in by_month.columns if c.endswith("DailyPnL")]
            if strategy_cols:
                by_month.set_index("Month")[strategy_cols].plot(kind="bar", stacked=True, figsize=(11,6))
                plt.xticks(rotation=45)
                plt.title("Monthly PnL by Strategy (Stacked)")
                plt.tight_layout()
                plt.savefig(fig3_path)
                plt.close()

            # Per-strategy equity charts
            per_strategy_figs = []
            for sid in dfs.keys():
                fig_path = os.path.join(CHART_DIR, f"equity_{sid}.png")
                col = f"{sid}_DailyPnL"
                if col in by_day:
                    plt.figure(figsize=(10,4))
                    plt.plot(by_day["TradeDate"], by_day[col].cumsum(), label=sid)
                    plt.title(f"Equity Curve - {sid}")
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    plt.savefig(fig_path)
                    plt.close()
                    per_strategy_figs.append((sid, fig_path))

        # ----- Build PDF report (report-style) -----
        styles = getSampleStyleSheet()
        cover_title = styles["Title"]
        normal = styles["Normal"]
        heading = styles["Heading2"]

        # Cover statistics
        dates = pd.to_datetime(by_day["TradeDate"]).dt.date
        start_date = dates.min()
        end_date = dates.max()
        num_strategies = len(dfs)
        total_pnl = float(by_day["TotalPnL"].sum())
        avg_daily = float(by_day["TotalPnL"].mean())
        strategy_list = list(dfs.keys())

        # Create PDF
        doc = SimpleDocTemplate(OUT_PDF, pagesize=portrait(A4), rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        story = []

        # Cover page
        story.append(Paragraph("Aggregated Strategy Performance Report", cover_title))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Date range: {start_date} to {end_date}", normal))
        story.append(Paragraph(f"Strategies included ({num_strategies}): {', '.join(strategy_list)}", normal))
        story.append(Paragraph(f"Total realized PnL: {total_pnl:,.2f}", normal))
        story.append(Paragraph(f"Average daily PnL: {avg_daily:,.2f}", normal))
        story.append(Spacer(1, 12))
        story.append(Paragraph("This report aggregates performance across multiple trading strategies, showing daily and monthly summaries, charts, and per-strategy contributions.", normal))
        story.append(PageBreak())

        # Section: Monthly summary chart and table (landscape)
        story.append(Paragraph("Monthly summary", heading))
        story.append(Spacer(1, 6))
        # Insert monthly chart (landscape page)
        story.append(Image(fig1_path, width=540, height=200))
        story.append(Spacer(1, 12))
        # Add monthly table
        # Build table data: headers + rows
        table_data = [by_month.columns.tolist()] + by_month.values.tolist()
        # Apply Table style
        tbl = Table(table_data, hAlign='LEFT')
        tbl.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#D9E1F2')),
            ('GRID',(0,0),(-1,-1),0.5,colors.grey),
            ('ALIGN',(1,1),(-1,-1),'RIGHT')
        ]))
        story.append(tbl)
        story.append(PageBreak())

        # Section: Equity curves (portrait ok)
        story.append(Paragraph("Equity curves (all strategies)", heading))
        story.append(Spacer(1,6))
        story.append(Image(fig2_path, width=520, height=260))
        story.append(PageBreak())

        # Section: Stacked monthly PnL
        if os.path.exists(fig3_path):
            story.append(Paragraph("Monthly PnL by Strategy (stacked)", heading))
            story.append(Spacer(1,6))
            story.append(Image(fig3_path, width=520, height=300))
            story.append(PageBreak())

        # Section: Per-strategy equity curves (each on its own page)
        for sid, fig in per_strategy_figs:
            story.append(Paragraph(f"Equity Curve - {sid}", heading))
            story.append(Spacer(1,6))
            story.append(Image(fig, width=520, height=260))
            story.append(PageBreak())

        # Final summary table (wide) — put in landscape
        summary_table_data = [by_month.columns.tolist()] + by_month.values.tolist()
        summary_table = Table(summary_table_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#D9E1F2')),
            ('GRID',(0,0),(-1,-1),0.5,colors.grey),
            ('ALIGN',(1,1),(-1,-1),'RIGHT')
        ]))
        # Use a new SimpleDocTemplate in landscape for this page and append the PDF content
        # To keep it simple, render the landscape table as its own document and then merge PDFs would be ideal,
        # but to keep dependencies minimal, we'll add the table with wider image size in portrait. 
        story.append(Paragraph("Monthly summary table (see Excel for full fidelity)", heading))
        story.append(Spacer(1,6))
        story.append(summary_table)

        # Build PDF
        doc.build(story)

        print(f"Saved Excel: {OUT_XLSX}")
        print(f"Saved PDF: {OUT_PDF}")
    
    def generate_trade_level_reports(self, strategy_obj):
        # Recompute intra-trade analysis using pnl_realized_y for all trades in NIFTY_S03_Final_Trade_Details_File.csv
        # Produces summary CSV/XLSX for all trades and a PDF report containing a summary table and plots for top 20 trades by max drawdown before profit.
        # Paths
        fname = f"{self.backtest_reports_dir}NIFTY_S03_Final_Trade_Details_File.csv"
        if not os.path.exists(fname):
            raise FileNotFoundError(f"{fname} not found in workspace. Available: {os.listdir('/mnt/data')}")

        # Load data
        df = pd.read_csv(fname)
        df.columns = [c.strip() for c in df.columns]

        # Detect columns
        trade_id_col = next((c for c in df.columns if c.lower()=="trade_id"), None)
        candle_time_col = next((c for c in df.columns if c.lower()=="candle_sttime"), None)
        pnl_realized_min_col = next((c for c in df.columns if c.lower()=="pnl_realized_y"), None)
        investment_col = next((c for c in df.columns if c.lower()=="investment_amount"), None)
        sell_datetime_y_col = next((c for c in df.columns if c.lower()=="sell_datetime_y"), None)

        if not all([trade_id_col, candle_time_col, pnl_realized_min_col]):
            raise ValueError("Required columns missing. Found columns: " + ", ".join(df.columns.tolist()))

        # Parse types
        df[candle_time_col] = pd.to_datetime(df[candle_time_col], errors='coerce')
        df[pnl_realized_min_col] = pd.to_numeric(df[pnl_realized_min_col], errors='coerce')
        if investment_col in df.columns:
            df[investment_col] = pd.to_numeric(df[investment_col], errors='coerce')

        groups = df.groupby(trade_id_col)
        summary_rows = []
        series_store = {}  # store realized series for top plotting if needed

        for tid, g in groups:
            g = g.sort_values(candle_time_col).reset_index(drop=True)
            times = pd.to_datetime(g[candle_time_col])
            realized = g[pnl_realized_min_col].fillna(0).astype(float).values
            if len(realized)==0:
                continue
            # running peak of realized PnL
            running_max = np.maximum.accumulate(realized)
            drawdowns = realized - running_max  # <=0
            # first time realized becomes positive
            profitable_idxs = np.where(realized>0)[0]
            profitable_found = len(profitable_idxs) > 0
            first_profit_time = pd.NaT
            cutoff_idx = len(realized)-1
            if profitable_found:
                first_profit_idx = int(profitable_idxs[0])
                first_profit_time = times.iloc[first_profit_idx]
                cutoff_idx = first_profit_idx
            else:
                first_profit_idx = None
            # max drawdown BEFORE first profit (consider up to cutoff_idx inclusive)
            seg_dd = drawdowns[:cutoff_idx+1] if len(drawdowns)>0 else np.array([0.0])
            max_dd_before_profit = float(seg_dd.min()) if len(seg_dd)>0 else 0.0
            max_dd_before_profit_abs = abs(max_dd_before_profit)
            # overall max realized profit/loss during trade
            max_realized_profit = float(np.nanmax(realized))
            max_realized_loss = float(np.nanmin(realized))
            t_max_profit = times.iloc[int(np.nanargmax(realized))] if not np.isnan(np.nanmax(realized)) else pd.NaT
            t_max_loss = times.iloc[int(np.nanargmin(realized))] if not np.isnan(np.nanmin(realized)) else pd.NaT
            # final realized PnL
            final_realized = float(realized[-1])
            # time to max drawdown: index of most negative in seg_dd (before profit)
            if len(seg_dd)>0:
                trough_idx = int(np.argmin(seg_dd))
                trough_time = times.iloc[trough_idx]
                # peak index corresponding to that drawdown: find last running_max peak before trough
                # running_max value at trough = running_max[trough_idx]; find first index where running_max == that value (peak index)
                peak_val = running_max[trough_idx]
                # find most recent index <= trough_idx where running_max == peak_val and realized == peak_val
                peak_idxs = np.where(running_max[:trough_idx+1] == peak_val)[0]
                peak_idx = int(peak_idxs[0]) if len(peak_idxs)>0 else 0
                peak_time = times.iloc[peak_idx]
                time_to_trough_min = (trough_time - times.iloc[0]).total_seconds()/60.0
                drawdown_duration_min = (trough_time - peak_time).total_seconds()/60.0
                # recovery: find first index after trough where realized >= peak_val (i.e., recovers to previous peak)
                recovery_idx = None
                for j in range(trough_idx+1, len(realized)):
                    if realized[j] >= peak_val:
                        recovery_idx = j
                        break
                recovery_time_min = (times.iloc[recovery_idx] - trough_time).total_seconds()/60.0 if recovery_idx is not None else np.nan
            else:
                trough_time = pd.NaT; peak_time = pd.NaT; time_to_trough_min = np.nan; drawdown_duration_min = np.nan; recovery_time_min = np.nan
            # drawdown relative to final realized
            drawdown_vs_final = (max_dd_before_profit_abs / abs(final_realized) * 100.0) if (final_realized!=0) else np.nan
            # percent of investment
            invest_amt = float(g[investment_col].iloc[0]) if investment_col in g.columns and pd.notna(g[investment_col].iloc[0]) else np.nan
            max_dd_pct_of_invest = (max_dd_before_profit_abs / invest_amt * 100.0) if (not np.isnan(invest_amt) and invest_amt!=0) else np.nan
            # duration overall
            start = times.iloc[0]
            end = times.iloc[-1] if (sell_datetime_y_col not in g.columns or pd.isna(g[sell_datetime_y_col].iloc[-1])) else pd.to_datetime(g[sell_datetime_y_col].iloc[-1])
            try:
                duration_min = (pd.to_datetime(end) - pd.to_datetime(start)).total_seconds()/60.0
            except:
                duration_min = np.nan
            summary_rows.append({
                trade_id_col: tid,
                "start_time": start,
                "end_time": end,
                "duration_min": duration_min,
                "first_profit_time": first_profit_time,
                "time_to_profit_min": ((pd.to_datetime(first_profit_time) - pd.to_datetime(start)).total_seconds()/60.0) if pd.notna(first_profit_time) else np.nan,
                "max_dd_before_profit": max_dd_before_profit,
                "max_dd_before_profit_abs": max_dd_before_profit_abs,
                "max_dd_before_profit_pct_of_investment": max_dd_pct_of_invest,
                "max_realized_profit": max_realized_profit,
                "time_of_max_realized_profit": t_max_profit,
                "max_realized_loss": max_realized_loss,
                "time_of_max_realized_loss": t_max_loss,
                "time_to_trough_min": time_to_trough_min,
                "drawdown_duration_min": drawdown_duration_min,
                "recovery_time_min": recovery_time_min,
                "final_realized_pnl": final_realized,
                "drawdown_vs_final_pct": drawdown_vs_final,
                "num_minutes": len(realized),
                "investment_amount": invest_amt
            })
            # store series for potential plotting
            series_store[tid] = {"times": times, "realized": realized, "running_max": running_max, "drawdown": drawdowns}

        # create DataFrame
        summary_df = pd.DataFrame(summary_rows)
        summary_df = summary_df.sort_values("max_dd_before_profit_abs", ascending=False).reset_index(drop=True)

        # Save outputs
        out_csv = f"{self.backtest_reports_dir}NIFTY_S03_intratrade_summary_realized_by_trade.csv"
        out_xlsx = f"{self.backtest_reports_dir}NIFTY_S03_intratrade_summary_realized_by_trade.xlsx"
        summary_df.to_csv(out_csv, index=False)
        summary_df.to_excel(out_xlsx, index=False)

        # Create plots for top 20 trades by max_dd_before_profit_abs
        os.makedirs(f"{self.backtest_reports_dir}NIFTY_S03_intratrade_realized_figs", exist_ok=True)
        top_n = min(20, len(summary_df))
        for i in range(top_n):
            tid = summary_df.iloc[i][trade_id_col]
            s = series_store[tid]
            x = np.arange(len(s["realized"]))
            plt.figure(figsize=(10,4))
            plt.plot(x, s["realized"], label="Realized PnL (minute)")
            plt.plot(x, s["running_max"], label="Running Max (Realized)")
            dd = np.array(s["drawdown"], dtype=float)
            if dd.size>0:
                dd = np.nan_to_num(dd, nan=0.0)
                plt.fill_between(x, dd, 0, alpha=0.25)
            plt.title(f"Trade {tid} - Realized PnL & Drawdown (index)")
            plt.xlabel("Minute index")
            plt.ylabel("Realized PnL")
            plt.legend()
            plt.tight_layout()
            plt.savefig(f"{self.backtest_reports_dir}NIFTY_S03_intratrade_realized_figs/trade_{tid}.png")
            plt.close()

        # Build PDF report containing top 20 table + plots
        pdf_path = f"{self.backtest_reports_dir}NIFTY_S03_intratrade_realized_report.pdf"
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph("NIFTY_S03 Intra-Trade Realized-PnL Analysis Report", styles['Title']))
        story.append(Spacer(1,12))
        intro = "This report uses minute-level realized PnL (`pnl_realized_y`) to compute intra-trade metrics including max drawdown before profitability, drawdown duration, recovery time, and final realized PnL. Top trades are ranked by max drawdown before profit."
        story.append(Paragraph(intro, styles['Normal']))
        story.append(Spacer(1,12))

        # Top 20 table
        top20 = summary_df.head(top_n)[[trade_id_col, "start_time", "end_time", "duration_min", "time_to_profit_min", "max_dd_before_profit_abs", "max_dd_before_profit_pct_of_investment", "final_realized_pnl"]]
        top20_display = top20.copy()
        top20_display["start_time"] = top20_display["start_time"].astype(str)
        top20_display["end_time"] = top20_display["end_time"].astype(str)
        top20_display = top20_display.fillna("").round(4)
        table_data = [top20_display.columns.tolist()] + top20_display.values.tolist()
        t = Table(table_data, hAlign='LEFT', repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.grey),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
                            ('ALIGN',(0,0),(-1,-1),'CENTER'),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
                            ('BOTTOMPADDING',(0,0),(-1,0),12),('GRID', (0,0), (-1,-1), 0.25, colors.black)]))
        story.append(t)
        story.append(PageBreak())

        # Insert plots
        figs = sorted([f for f in os.listdir(f"{self.backtest_reports_dir}NIFTY_S03_intratrade_realized_figs") if f.endswith(".png")])[:top_n]
        for f in figs:
            story.append(Paragraph(f, styles['Heading2']))
            story.append(Image(os.path.join(f"{self.backtest_reports_dir}NIFTY_S03_intratrade_realized_figs", f), width=480, height=220))
            story.append(Spacer(1,12))
            story.append(PageBreak())

        doc.build(story)

        # Display outputs and a sample of the summary
        #caas_jupyter_tools.display_dataframe_to_user("Realized intra-trade summary (top 50 by drawdown)", summary_df.head(50))
        #caas_jupyter_tools.display_dataframe_to_user("Saved outputs", pd.DataFrame([{"csv": out_csv, "xlsx": out_xlsx, "figs_folder": f"{self.backtest_reports_dir}NIFTY_S03_intratrade_realized_figs", "pdf": pdf_path}] ))

        #{"csv": out_csv, "xlsx": out_xlsx, "figs": f"{self.backtest_reports_dir}NIFTY_S03_intratrade_realized_figs", "pdf": pdf_path, "top_plots": top_n, "rows": len(summary_df)}

    def calc_optimal_thresholds(self, directory_path=None):
        """
        Reads all CSV files from a directory, aggregates max profit/loss data,
        and calculates optimal 75th percentile thresholds.

        Args:
            directory_path (str): The path to the folder containing your CSV files.

        Returns:
            dict: A dictionary containing the calculated thresholds.
        """
        # Find all CSV files in the specified directory
        all_files = glob.glob(os.path.join(self.trade_data_details_dir, "*.csv"))

        if not all_files:
            return {"Error": f"No CSV files found in the directory: {self.trade_data_details_dir}"}

        list_of_dfs = []

        for filename in all_files:
            # Read only the necessary columns to save memory
            df = pd.read_csv(filename, usecols=['max_profit_unrealized', 'max_loss_unrealized'])
            list_of_dfs.append(df)

        # Concatenate all DataFrames into a single aggregate DataFrame
        aggregate_df = pd.concat(list_of_dfs, ignore_index=True)

        # Filter for only the non-zero, negative values for losses
        negative_losses = aggregate_df['max_loss_unrealized']
        # We invert the values for simpler percentile calculation (e.g., -10 becomes 10)
        # loss_magnitudes = negative_losses[negative_losses < 0].abs()
        loss_magnitudes = negative_losses[negative_losses < 0]

        # Filter for only the non-zero, positive values for profits
        positive_profits = aggregate_df['max_profit_unrealized']
        profits = positive_profits[positive_profits > 0]

        if loss_magnitudes.empty or profits.empty:
            return {"Error": "Insufficient data in one or both columns to calculate percentiles."}

        # Calculate the 75th percentile for loss magnitude
        # 75th percentile for loss helps find a threshold where 75% of losses were smaller
        # In other words, identify and cut losing trades relatively early
        loss_threshold_magnitude = loss_magnitudes.quantile(0.78)
        # The actual threshold value needs to be negative again, use this if inverting negative values above
        # optimal_loss_threshold = -loss_threshold_magnitude
        optimal_loss_threshold = loss_threshold_magnitude

        # Calculate the 25th percentile for profit
        # 25th percentile for profit means 25% of max profits were below this value
        # In other words, we aim to capture larger profits
        optimal_profit_threshold = profits.quantile(0.34)

        return {
            "Optimal Loss Threshold (75th Percentile)": optimal_loss_threshold,
            "Optimal Profit Threshold (25th Percentile)": optimal_profit_threshold,
            "Total Trades Analyzed (Approx Rows)": len(aggregate_df)
        }


    def calc_unrealized_final_pnl_left_on_table(self, directory_path=None):
        results = []
        def get_numeric_key(filename):
            # Extracts all numbers from the filename and converts them to integers
            numbers = re.findall(r"\d+", filename)
            return [int(num) for num in numbers] if numbers else filename


        # Sort the files numerically before looping
        sorted_filenames = sorted(
            os.listdir(self.trade_data_details_dir), key=get_numeric_key
        )
        # Iterate through all files in the directory
        # for filename in os.listdir(self.trade_data_details_dir):
        for filename in sorted_filenames:
            if filename.endswith(".csv"):
                file_path = os.path.join(self.trade_data_details_dir, filename)

                try:
                    df = pd.read_csv(file_path)
                    
                    if df.empty:
                        continue

                    # Check the last row for a positive pnl_realized
                    final_pnl = df['pnl_realized'].iloc[-1]
                    buy_dt = df['buy_datetime'].iloc[-1] if 'buy_datetime' in df.columns else 'N/A'
                    sell_dt = df['sell_datetime'].iloc[-1] if 'sell_datetime' in df.columns else 'N/A'

                    if final_pnl > 0:
                        # Find the lowest (most negative) max_loss_unrealized value
                        lowest_drawdown = df['max_loss_unrealized'].min()
                        highest_runup = df['max_profit_unrealized'].max()

                        results.append({
                            'file': filename,
                            'buy_datetime': buy_dt,
                            'sell_datetime': sell_dt,
                            'final_pnl': final_pnl,
                            'highest_unrealized_profit': highest_runup,
                            'profit_left_on_the_table': highest_runup - final_pnl,
                            'lowest_unrealized_loss': lowest_drawdown,
                            'loss_salvaged_from_lows': 0.0
                        })
                    elif final_pnl < 0:
                        # Find the lowest (most negative) max_loss_unrealized value
                        lowest_drawdown = df['max_loss_unrealized'].min()
                        highest_runup = df['max_profit_unrealized'].max()

                        results.append({
                            'file': filename,
                            'buy_datetime': buy_dt,
                            'sell_datetime': sell_dt,
                            'final_pnl': final_pnl,
                            'highest_unrealized_profit': highest_runup,
                            'profit_left_on_the_table': 0.0,
                            'lowest_unrealized_loss': lowest_drawdown,
                            'loss_salvaged_from_lows': final_pnl - lowest_drawdown
                        })
                except Exception as e:
                    print(f"Error processing {filename}: {e}")

        output_csv = os.path.join(self.backtest_reports_dir, "unrealized_final_pnl_analysis.csv")
        pd.DataFrame(results).to_csv(output_csv, index=False)

        return pd.DataFrame(results)

    # Usage
    # folder_path = 'path/to/your/csv/folder'
    # analysis_df = analyze_drawdown_on_profitable_trades(folder_path)
    # print(analysis_df)

    """
    nifty_03_signal_trade_file = os.path.join(__backtestconfig__.TRADE_DATA_FILE_DIR, "NIFTY_S03_Signal_Trade_File.csv")
    nifty_04_signal_trade_file = os.path.join(__backtestconfig__.TRADE_DATA_FILE_DIR, "NIFTY_S04_Signal_Trade_File.csv")
    nifty_05_signal_trade_file = os.path.join(__backtestconfig__.TRADE_DATA_FILE_DIR, "NIFTY_S05_Signal_Trade_File.csv")
    nifty_06_signal_trade_file = os.path.join(__backtestconfig__.TRADE_DATA_FILE_DIR, "NIFTY_S06_Signal_Trade_File.csv")
    nifty_06_signal_trade_file = os.path.join(__backtestconfig__.TRADE_DATA_FILE_DIR, "NIFTY_S06_Signal_Trade_File.csv")
    nifty_07_signal_trade_file = os.path.join(__backtestconfig__.TRADE_DATA_FILE_DIR, "NIFTY_S07_Signal_Trade_File.csv")
    nifty_08_signal_trade_file = os.path.join(__backtestconfig__.TRADE_DATA_FILE_DIR, "NIFTY_S08_Signal_Trade_File.csv")

    self.df_nf03 = pd.read_csv(nifty_03_signal_trade_file, \
                                    dtype={'trade_id': str, 'trade_date': str, 'buy_datetime': str, 'sell_datetime': str, 'investment_amount': float, \
                                            'instrument_key': str, 'trading_symbol': str, 'lot_size': int,'num_of_lots': int, \
                                            'overall_pnl': float, 'pnl_realized': float, 'slippage': float, 'max_unrealized_profit_during_trade': float, 'max_unrealized_loss_during_trade': float})

    self.df_nf04 = pd.read_csv(nifty_04_signal_trade_file, \
                                    dtype={'trade_id': str, 'trade_date': str, 'buy_datetime': str, 'sell_datetime': str, 'investment_amount': float, \
                                            'instrument_key': str, 'trading_symbol': str, 'lot_size': int,'num_of_lots': int, \
                                            'overall_pnl': float, 'pnl_realized': float, 'slippage': float, 'max_unrealized_profit_during_trade': float, 'max_unrealized_loss_during_trade': float})

    self.df_nf05 = pd.read_csv(nifty_05_signal_trade_file, \
                                    dtype={'trade_id': str, 'trade_date': str, 'buy_datetime': str, 'sell_datetime': str, 'investment_amount': float, \
                                            'instrument_key': str, 'trading_symbol': str, 'lot_size': int,'num_of_lots': int, \
                                            'overall_pnl': float, 'pnl_realized': float, 'slippage': float, 'max_unrealized_profit_during_trade': float, 'max_unrealized_loss_during_trade': float})

    self.df_nf06 = pd.read_csv(nifty_06_signal_trade_file, \
                                    dtype={'trade_id': str, 'trade_date': str, 'buy_datetime': str, 'sell_datetime': str, 'investment_amount': float, \
                                            'instrument_key': str, 'trading_symbol': str, 'lot_size': int,'num_of_lots': int, \
                                            'overall_pnl': float, 'pnl_realized': float, 'slippage': float, 'max_unrealized_profit_during_trade': float, 'max_unrealized_loss_during_trade': float})

    self.df_nf07 = pd.read_csv(nifty_07_signal_trade_file, \
                                    dtype={'trade_id': str, 'trade_date': str, 'buy_datetime': str, 'sell_datetime': str, 'investment_amount': float, \
                                            'instrument_key': str, 'trading_symbol': str, 'lot_size': int,'num_of_lots': int, \
                                            'overall_pnl': float, 'pnl_realized': float, 'slippage': float, 'max_unrealized_profit_during_trade': float, 'max_unrealized_loss_during_trade': float})

    self.df_nf08 = pd.read_csv(nifty_08_signal_trade_file, \
                                    dtype={'trade_id': str, 'trade_date': str, 'buy_datetime': str, 'sell_datetime': str, 'investment_amount': float, \
                                            'instrument_key': str, 'trading_symbol': str, 'lot_size': int,'num_of_lots': int, \
                                            'overall_pnl': float, 'pnl_realized': float, 'slippage': float, 'max_unrealized_profit_during_trade': float, 'max_unrealized_loss_during_trade': float})

    merged_df_nf03_nf_04 = pd.concat([self.df_nf03, self.df_nf04], ignore_index=True)
    merged_df_nf03_nf_04['buy_datetime'] = pd.to_datetime(merged_df_nf03_nf_04['buy_datetime'])
    sorted_df_nf03_nf_04 = merged_df_nf03_nf_04.sort_values(by='buy_datetime', ascending=True)
    pnl_realized_nf03_nf_04 = sorted_df_nf03_nf_04['pnl_realized'].sum()
    sum_by_date = merged_df_nf03_nf_04.groupby('trade_date')['pnl_realized'].sum()
    print(f"NIFTY03 & NIFTY04 - Sum by Date: {sum_by_date}")
    print(f"NIFTY03 & NIFTY04 - Realized PnL: {pnl_realized_nf03_nf_04}")
    
    merged_df_nf05_nf_06 = pd.concat([self.df_nf05, self.df_nf06], ignore_index=True)
    merged_df_nf05_nf_06['buy_datetime'] = pd.to_datetime(merged_df_nf05_nf_06['buy_datetime'])
    sorted_df_nf05_nf_06 = merged_df_nf05_nf_06.sort_values(by='buy_datetime', ascending=True)
    pnl_realized_nf05_nf_06 = sorted_df_nf05_nf_06['pnl_realized'].sum()
    sum_by_date = merged_df_nf05_nf_06.groupby('trade_date')['pnl_realized'].sum()
    print(f"NIFTY05 & NIFTY06 - Sum by Date: {sum_by_date}")
    print(f"NIFTY05 & NIFTY06 - Realized PnL: {pnl_realized_nf05_nf_06}")

    merged_df_nf07_nf_08 = pd.concat([self.df_nf07, self.df_nf08], ignore_index=True)
    merged_df_nf07_nf_08['buy_datetime'] = pd.to_datetime(merged_df_nf07_nf_08['buy_datetime'])
    sorted_df_nf07_nf_08 = merged_df_nf07_nf_08.sort_values(by='buy_datetime', ascending=True)
    pnl_realized_nf07_nf_08 = sorted_df_nf07_nf_08['pnl_realized'].sum()
    sum_by_date = merged_df_nf07_nf_08.groupby('trade_date')['pnl_realized'].sum()
    print(f"NIFTY07 & NIFTY08 - Sum by Date: {sum_by_date}")
    print(f"NIFTY07 & NIFTY08 - Realized PnL: {pnl_realized_nf07_nf_08}")
    """

