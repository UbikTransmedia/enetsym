import tkinter as tk
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import random
import time
from matplotlib.colors import Normalize
import matplotlib.cm as cm

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
            G.nodes[node]['carga_max'] = float('inf')  # Carga máxima infinita
        elif node in stations:
            G.nodes[node]['tipo'] = 'estacion'
            G.nodes[node]['carga_max'] = random.uniform(50, 100)
            G.nodes[node]['carga_actual'] = random.uniform(0, G.nodes[node]['carga_max'])
            G.nodes[node]['salud_bateria'] = random.uniform(0.5, 1.0)
        else:
            G.nodes[node]['tipo'] = 'distribuidor'
            G.nodes[node]['carga_max'] = random.uniform(100, 200)
            G.nodes[node]['carga_actual'] = random.uniform(0, G.nodes[node]['carga_max'])
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
        G.nodes[node]['carga_actual'] = random.uniform(0, G.nodes[node]['carga_max'])
        G.nodes[node]['salud_bateria'] = random.uniform(0.5, 1.0)
    return G

def agregar_controladores(G):
    num_controladores = max(1, int(0.05 * len(G.nodes())))  # 5% de los nodos como controladores
    nodos_disponibles = list(G.nodes())
    controladores = random.sample(nodos_disponibles, num_controladores)
    for node in controladores:
        G.nodes[node]['tipo'] = 'controlador'
        G.nodes[node]['carga_actual'] = 0
        G.nodes[node]['carga_max'] = float('inf')
        # Conectar a varios nodos aleatorios
        num_conexiones = random.randint(5, 15)
        nodos_a_conectar = random.sample(nodos_disponibles, num_conexiones)
        for n in nodos_a_conectar:
            G.add_edge(node, n)
    return G

def posicionar_nodos(G):
    # Usar un layout de red radial para colocar los nodos terminales en la periferia
    tipos = nx.get_node_attributes(G, 'tipo')
    estaciones = [node for node, tipo in tipos.items() if tipo in ['estacion', 'consumidor']]
    controladores = [node for node, tipo in tipos.items() if tipo == 'controlador']
    distribuidores = [node for node, tipo in tipos.items() if tipo == 'distribuidor']
    suministradores = [node for node, tipo in tipos.items() if tipo == 'suministrador']

    # Crear capas
    layers = [suministradores + controladores, distribuidores, estaciones]

    # Usar shell_layout para posicionar los nodos en capas concéntricas
    pos = nx.shell_layout(G, nlist=layers)
    return pos

def dibujar_red():
    ax.clear()

    # Obtener valores de carga para normalizar colores
    cargas = [G.nodes[node].get('carga_actual', 0) for node in G.nodes()]
    cargas_max = [G.nodes[node].get('carga_max', 100) for node in G.nodes()]
    cargas_relativas = [c / m if m != 0 else 0 for c, m in zip(cargas, cargas_max)]

    norm = Normalize(vmin=0, vmax=1)
    cmap = cm.get_cmap('YlOrRd')  # Colormap de amarillo a rojo

    node_colors = []
    node_sizes = []
    for node in G.nodes():
        tipo = G.nodes[node]['tipo']
        carga_relativa = G.nodes[node].get('carga_actual', 0) / G.nodes[node].get('carga_max', 1)
        # Calcular color
        color_intensity = norm(carga_relativa)
        color = cmap(color_intensity)
        node_colors.append(color)

        # Tamaño del nodo proporcional a la carga
        size = 100 + carga_relativa * 200
        node_sizes.append(size)

    # Colorear los controladores de manera diferente
    for i, node in enumerate(G.nodes()):
        if G.nodes[node]['tipo'] == 'controlador':
            node_colors[i] = 'purple'
            node_sizes[i] = 300

    nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.3, width=0.5)
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, ax=ax)
    ax.set_axis_off()
    canvas.draw()

    # Actualizar el contador de tiempo en la etiqueta
    elapsed_time = time.time() - start_time
    time_label.config(text=f"Unidad de tiempo: {t}\nTiempo transcurrido: {elapsed_time:.2f} s")

def restar_carga(nodo, consumo, visitados):
    if nodo in visitados:
        return
    visitados.add(nodo)
    tipo = G.nodes[nodo]['tipo']
    if tipo == 'suministrador' or tipo == 'controlador':
        return
   
