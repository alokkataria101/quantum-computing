from data_loader import load_stock_data
from analyzer import StockAnalyzer
from visualization import StockVisualizer


df = load_stock_data(
    "RELIANCE",
    180
)


analyzer = StockAnalyzer(
    df,
    "RELIANCE"
)


analyzer.run_analysis()


visualizer = StockVisualizer(
    analyzer
)


visualizer.generate_all()
