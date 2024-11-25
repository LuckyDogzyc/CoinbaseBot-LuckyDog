from restClient import client

portfolios = client.get_portfolios()
print(portfolios)