from data_loader import load_stock_data
from analyzer import StockAnalyzer
from report import ReportGenerator


df = load_stock_data(
    "RELIANCE",
    180
)


analyzer = StockAnalyzer(
    df,
    "RELIANCE"
)


analyzer.run_analysis()


report = ReportGenerator(
    analyzer
)


report.print_summary()

report.export_csv()

report.export_json()
