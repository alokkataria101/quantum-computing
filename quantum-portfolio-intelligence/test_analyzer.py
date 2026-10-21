from data_loader import load_stock_data
from analyzer import StockAnalyzer

df = load_stock_data("RELIANCE",180)

analyzer = StockAnalyzer(df,"RELIANCE")

analyzer.run_analysis()

analyzer.print_debug()