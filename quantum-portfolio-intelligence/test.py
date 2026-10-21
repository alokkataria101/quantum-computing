from portfolio import PortfolioAnalyzer

from quantum.portfolio_quantum import QuantumPortfolio
from quantum.fidelity_matrix import FidelityMatrix
from quantum.fidelity_heatmap import FidelityHeatmap

portfolio = PortfolioAnalyzer(

    ["RELIANCE","TCS","INFY","HDFCBANK"],

    365

)

portfolio.analyze()

qp = QuantumPortfolio(portfolio)

qp.build()

matrix = FidelityMatrix(qp)

matrix.calculate()

heatmap = FidelityHeatmap(matrix)

heatmap.save()
