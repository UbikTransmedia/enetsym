import tkinter as tk
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import random

def generar_red(seed, centralizacion):
    random.seed(seed)
    np.random.seed(seed)
    if centralizacion == 'centralizada':
        G = nx.barabasi_albert_graph(50, 3, seed=seed)
    elif centralizacion == 'descentralizada':
        G = nx.erdos_renyi_graph(50, 0.1, seed=seed)
    else:
        G = nx.random_regular_graph(3, 50, seed=seed)
    return G

def clasificar_nodos(G):
    degrees = dict(G.degree())
    sorted_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
    num_nodes = len(G.nodes())
    suppliers_num = max(1, int(0.1 * num_nodes))

    suppliers = [node for node, deg in sorted_nodes[:suppliers_num]]
    stations = [node for node, deg in degrees.items() if deg == 1]
    distributors = [node for node in G.nodes() if node not in suppliers and node not in stations]

    for node in G.nodes():
        if node in suppliers:
            G.nodes[node]['tipo'] = 'suministrador'
            G.nodes[node]['produccion'] = random.uniform(5, 10)
            G.nodes[node]['fase'] = random.uniform(0, 2*np.pi)
            G.nodes[node]['carga_actual'] = 0
        elif node in stations:
            G.nodes[node]['tipo'] = 'estacion'
            G.nodes[node]['carga_max'] = random.uniform(50, 100)
            G.nodes[node]['carga_actual'] = random.uniform(0, G.nodes[node]['carga_max'])
            G.nodes[node]['salud_bateria'] = random.uniform(0.5, 1.0)
        else:
            G.nodes[node]['tipo'] = 'distribuidor'
            G.nodes[node]['carga_max'] = random.uniform(100, 200)
            G.nodes[node]['carga_actual'] = 0
            G.nodes[node]['salud'] = random.uniform(0.5, 1.0)
    return G

def convertir_estaciones_en_consumidores(G):
    estaciones = [node for node in G.nodes() if G.nodes[node]['tipo'] == 'estacion']
    num_estaciones = len(estaciones)

    if num_estaciones == 0:
        return G  # No hay estaciones para convertir en consumidores

    num_consumidores = min(num_estaciones, max(1, int(0.1 * num_estaciones)))
    consumidores = random.sample(estaciones, num_consumidores)
    for node in consumidores:
        G.nodes[node]['tipo'] = 'consumidor'
        G.nodes[node]['consumo'] = random.uniform(5, 10)
        G.nodes[node]['carga_actual'] = 0
        G.nodes[node].pop('carga_max', None)
        G.nodes[node].pop('salud_bateria', None)
    return G

def dibujar_red():
    plt.clf()
    node_colors = []
    node_sizes = []
    for node in G.nodes():
        tipo = G.nodes[node]['tipo']
        carga_actual = G.nodes[node].get('carga_actual', 0)
        if tipo == 'suministrador':
            node_colors.append('green')
            node_sizes.append(300)
        elif tipo == 'distribuidor':
            node_colors.append('blue')
            size = 100 + carga_actual * 2
            node_sizes.append(size)
        elif tipo == 'estacion':
            node_colors.append('orange')
            size = 100 + carga_actual * 2
            node_sizes.append(size)
        elif tipo == 'consumidor':
            node_colors.append('red')
            node_sizes.append(300)
        else:
            node_colors.append('grey')
            node_sizes.append(100)
    nx.draw(G, pos, with_labels=False, node_color=node_colors, node_size=node_sizes)
    canvas.draw()

def restar_carga(nodo, consumo, visitados):
    if nodo in visitados:
        return
    visitados.add(nodo)
    tipo = G.nodes[nodo]['tipo']
    if tipo == 'suministrador':
        return
    else:
        carga_actual = G.nodes[nodo]['carga_actual']
        if carga_actual >= consumo:
            G.nodes[nodo]['carga_actual'] -= consumo
        else:
            deficit = consumo - carga_actual
            G.nodes[nodo]['carga_actual'] = 0
            vecinos = list(G.neighbors(nodo))
            vecinos = [n for n in vecinos if G.nodes[n]['tipo'] != 'consumidor' and n not in visitados]
            if vecinos:
                vecino = random.choice(vecinos)
                restar_carga(vecino, deficit, visitados)

def actualizar():
    global t
    t += dt

    for node in G.nodes():
        G.nodes[node]['carga_recibida'] = 0

    for node in G.nodes():
        if G.nodes[node]['tipo'] == 'suministrador':
            produccion_base = G.nodes[node]['produccion']
            fase = G.nodes[node]['fase']
            produccion = produccion_base * np.sin(2 * np.pi * t + fase)
            if produccion < 0:
                produccion = 0
            vecinos = list(G.neighbors(node))
            if vecinos:
                carga_por_vecino = produccion / len(vecinos)
                for vecino in vecinos:
                    if G.nodes[vecino]['tipo'] != 'suministrador':
                        G.nodes[vecino]['carga_recibida'] += carga_por_vecino

    for node in G.nodes():
        if G.nodes[node]['tipo'] == 'distribuidor':
            G.nodes[node]['carga_actual'] += G.nodes[node]['carga_recibida']
            if G.nodes[node]['carga_actual'] > G.nodes[node]['carga_max']:
                G.nodes[node]['carga_actual'] = G.nodes[node]['carga_max']
            G.nodes[node]['carga_a_distribuir'] = G.nodes[node]['carga_actual']
            G.nodes[node]['carga_actual'] = 0

    for node in G.nodes():
        if G.nodes[node]['tipo'] == 'distribuidor':
            carga_a_distribuir = G.nodes[node]['carga_a_distribuir']
            vecinos = list(G.neighbors(node))
            vecinos = [n for n in vecinos if G.nodes[n]['tipo'] != 'suministrador']
            if vecinos:
                carga_por_vecino = carga_a_distribuir / len(vecinos)
                for vecino in vecinos:
                    G.nodes[vecino]['carga_recibida'] += carga_por_vecino
            G.nodes[node]['carga_a_distribuir'] = 0

    for node in G.nodes():
        if G.nodes[node]['tipo'] == 'estacion':
            G.nodes[node]['carga_actual'] += G.nodes[node]['carga_recibida']
            if G.nodes[node]['carga_actual'] > G.nodes[node]['carga_max']:
                G.nodes[node]['carga_actual'] = G.nodes[node]['carga_max']

    for node in G.nodes():
        if G.nodes[node]['tipo'] == 'consumidor':
            consumo = G.nodes[node]['consumo']
            vecinos = list(G.neighbors(node))
            if vecinos:
                distribuidor = vecinos[0]
                restar_carga(distribuidor, consumo, set([node]))

    dibujar_red()
    root.after(int(dt * 1000), actualizar)

# Configuración de la ventana principal
root = tk.Tk()
root.geometry("1080x780")
root.title("Red de Nodos")

# Generar la red
seed = 42
centralizacion = 'centralizada'  # Opciones: 'centralizada', 'descentralizada', 'distribuida'

G = generar_red(seed, centralizacion)
G = clasificar_nodos(G)
G = convertir_estaciones_en_consumidores(G)

# Posiciones de los nodos
pos = nx.spring_layout(G, seed=seed)

# Figura de matplotlib
fig = plt.figure(figsize=(8,6))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

t = 0  # Tiempo inicial
dt = 0.01  # Intervalo de tiempo en segundos

# Inicializar 'carga_a_distribuir' y 'carga_actual' para todos los nodos
for node in G.nodes():
    G.nodes[node]['carga_a_distribuir'] = 0
    if 'carga_actual' not in G.nodes[node]:
        G.nodes[node]['carga_actual'] = 0

actualizar()

root.mainloop()
