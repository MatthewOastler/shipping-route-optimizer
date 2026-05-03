def calculate_edge_cost(e): return e.get('fuel_cost',0)+e.get('canal_fee',0)+e.get('weather_risk',0)+e.get('piracy_risk',0)+e.get('carbon_cost',0)
