import matplotlib.pyplot as plt
import networkx as nx

def plot_route(G,path):
 pos=nx.spring_layout(G,seed=1)
 nx.draw(G,pos,with_labels=True,node_color='lightblue')
 nx.draw_networkx_edges(G,pos,edgelist=list(zip(path,path[1:])),edge_color='red',width=3)
 plt.show()
