from data_loader import load_stock_data

df = load_stock_data("RELIANCE",180)

print(df.head())

print()

print(df.tail())

print()

print(df.info())
