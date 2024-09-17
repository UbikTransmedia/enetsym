import tkinter as tk
import networkx as nx
# Importar FigureCanvasTkAgg y NavigationToolbar2TkAgg dependiendo de la versión de matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import random
import time

def generar_red(seed, centralizacion, num_nodos):
    random.seed(seed)
    np.random.seed(seed)
    if centralizacion == 'centralizada':
        m = max(1, int(0.01 * num_nodos))
        G = nx.barabasi_albert_graph(num_nodos, m, seed=seed)
    elif centralizacion == 'descentralizada':
        p = 0.005  # Ajustar p para redes grandes
        G = nx.erdos_renyi_graph(num_nodos, p, seed=seed)
    else:
        d = 3  # Grado regular
        G = nx.random_regular_graph(d, num_nodos, seed=seed)
    return G

def clasificar_nodos(G):
    degrees = dict(G.degree())
    sorted_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
    num_nodes = len(G.nodes())
    suppliers_num = max(1, int(0.05 * num_nodes))  # 5% como suministradores

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
    ax.clear()
    node_colors = []
    node_sizes = []
    for node in G.nodes():
        tipo = G.nodes[node]['tipo']
        carga_actual = G.nodes[node].get('carga_actual', 0)
        if tipo == 'suministrador':
            node_colors.append('green')
            node_sizes.append(50)
        elif tipo == 'distribuidor':
            node_colors.append('blue')
            size = 20 + carga_actual * 0.1
            node_sizes.append(size)
        elif tipo == 'estacion':
            node_colors.append('orange')
            size = 20 + carga_actual * 0.1
            node_sizes.append(size)
        elif tipo == 'consumidor':
            node_colors.append('red')
            node_sizes.append(50)
        else:
            node_colors.append('grey')
            node_sizes.append(20)
    nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.3)
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, ax=ax)
    ax.set_axis_off()
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
    t += 1  # Avanza 1 unidad de tiempo en cada iteración

    for node in G.nodes():
        G.nodes[node]['carga_recibida'] = 0

    # Producción de los suministradores
    for node in G.nodes():
        if G.nodes[node]['tipo'] == 'suministrador':
            produccion_base = G.nodes[node]['produccion']
            fase = G.nodes[node]['fase']
            produccion = produccion_base * np.sin(0.1 * t + fase)  # Ajuste de frecuencia
            if produccion < 0:
                produccion = 0
            vecinos = list(G.neighbors(node))
            if vecinos:
                carga_por_vecino = produccion / len(vecinos)
                for vecino in vecinos:
                    if G.nodes[vecino]['tipo'] != 'suministrador':
                        G.nodes[vecino]['carga_recibida'] += carga_por_vecino

    # Actualización de distribuidores
    for node in G.nodes():
        if G.nodes[node]['tipo'] == 'distribuidor':
            G.nodes[node]['carga_actual'] += G.nodes[node]['carga_recibida']
            if G.nodes[node]['carga_actual'] > G.nodes[node]['carga_max']:
                G.nodes[node]['carga_actual'] = G.nodes[node]['carga_max']
            G.nodes[node]['carga_a_distribuir'] = G.nodes[node]['carga_actual']
            G.nodes[node]['carga_actual'] = 0

    # Distribución de carga de los distribuidores
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

    # Actualización de estaciones
    for node in G.nodes():
        if G.nodes[node]['tipo'] == 'estacion':
            G.nodes[node]['carga_actual'] += G.nodes[node]['carga_recibida']
            if G.nodes[node]['carga_actual'] > G.nodes[node]['carga_max']:
                G.nodes[node]['carga_actual'] = G.nodes[node]['carga_max']

    # Consumo de los consumidores
    for node in G.nodes():
        if G.nodes[node]['tipo'] == 'consumidor':
            consumo = G.nodes[node]['consumo']
            vecinos = list(G.neighbors(node))
            if vecinos:
                distribuidor = vecinos[0]
                restar_carga(distribuidor, consumo, set([node]))

    # Dibujar la red
    dibujar_red()

    # Programar la siguiente actualización
    root.after(int(dt * 1000), actualizar)

# Configuración de la ventana principal
root = tk.Tk()
root.geometry("1080x780")
root.title("Red de Nodos")

# Generar la red
seed = 42
centralizacion = 'centralizada'  # Opciones: 'centralizada', 'descentralizada', 'distribuida'
num_nodos = 1000  # Número de nodos

G = generar_red(seed, centralizacion, num_nodos)
G = clasificar_nodos(G)
G = convertir_estaciones_en_consumidores(G)

# Posiciones de los nodos
pos = nx.spring_layout(G, seed=seed, k=0.15, iterations=20)

# Figura de matplotlib
fig, ax = plt.subplots(figsize=(8,6))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

t = 0  # Tiempo inicial
dt = 0.01  # Intervalo de tiempo en segundos

# Inicializar 'carga_a_distribuir' y 'carga_actual' para todos los nodos
for node in G.nodes():
    G.nodes[node]['carga_a_distribuir'] = 0
    if 'carga_actual' not in G.nodes[node]:
        G.nodes[node]['carga_actual'] = 0

# Iniciar la actualización y el dibujo
actualizar()

root.mainloop()
