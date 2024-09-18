import tkinter as tk
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import random
import time
from matplotlib.colors import Normalize
import matplotlib.cm as cm
import sys
import traceback

try:
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
                G.nodes[node]['capacity'] = random.uniform(5, 10)  # Capacidad para generar energía
                G.nodes[node]['fase'] = random.uniform(0, 2*np.pi)
                G.nodes[node]['carga_actual'] = 0
                G.nodes[node]['carga_max'] = G.nodes[node]['capacity']  # Carga máxima es su capacidad
            elif node in stations:
                G.nodes[node]['tipo'] = 'estacion'
                G.nodes[node]['carga_max'] = random.uniform(50, 100)
                G.nodes[node]['carga_actual'] = 0.5 * G.nodes[node]['carga_max']  # Comienza al 50% de carga
                G.nodes[node]['fase'] = random.uniform(0, 2*np.pi)  # Fase para su función seno
            else:
                G.nodes[node]['tipo'] = 'distribuidor'
                G.nodes[node]['carga_max'] = random.uniform(100, 200)
                G.nodes[node]['carga_actual'] = random.uniform(0, G.nodes[node]['carga_max'])
        return G

    def posicionar_nodos(G):
        # Usar un layout de red radial para colocar los nodos terminales en la periferia
        tipos = nx.get_node_attributes(G, 'tipo')
        estaciones = [node for node, tipo in tipos.items() if tipo == 'estacion']
        distribuidores = [node for node, tipo in tipos.items() if tipo == 'distribuidor']
        suministradores = [node for node, tipo in tipos.items() if tipo == 'suministrador']

        # Crear capas
        layers = [suministradores, distribuidores, estaciones]

        # Verificar que las capas no estén vacías
        layers = [layer for layer in layers if layer]

        # Usar shell_layout para posicionar los nodos en capas concéntricas
        pos = nx.shell_layout(G, nlist=layers)
        return pos

    def dibujar_red():
        ax.clear()

        # Obtener valores de carga para normalizar colores
        cargas = []
        cargas_max = []
        for node in G.nodes():
            cargas.append(G.nodes[node].get('carga_actual', 0))
            cargas_max.append(G.nodes[node].get('carga_max', 1))
        cargas_relativas = [c / m if m != 0 else 0 for c, m in zip(cargas, cargas_max)]

        norm = Normalize(vmin=0, vmax=1)
        cmap = cm.get_cmap('YlOrRd')  # Colormap de amarillo a rojo

        node_colors = []
        node_sizes = []
        for node in G.nodes():
            tipo = G.nodes[node]['tipo']
            carga_actual = G.nodes[node].get('carga_actual', 0)
            carga_max = G.nodes[node].get('carga_max', 1)
            carga_relativa = carga_actual / carga_max if carga_max != 0 else 0
            # Calcular color
            color_intensity = norm(carga_relativa)
            color = cmap(color_intensity)
            node_colors.append(color)
            # Tamaño del nodo proporcional a la carga
            size = 100 + carga_relativa * 200
            node_sizes.append(size)

        nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.3, width=0.5)
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, ax=ax)
        ax.set_axis_off()
        canvas.draw()

        # Actualizar el contador de tiempo en la etiqueta
        elapsed_time = time.time() - start_time
        time_label.config(text=f"Unidad de tiempo: {t}\nTiempo transcurrido: {elapsed_time:.2f} s")

    def actualizar():
        global t, pending_station_changes
        t += 1  # Avanza 1 unidad de tiempo en cada iteración

        # Reiniciar carga_recibida para todos los nodos
        for node in G.nodes():
            G.nodes[node]['carga_recibida'] = 0

        # Producción de los suministradores
        for node in G.nodes():
            if G.nodes[node]['tipo'] == 'suministrador':
                capacity = G.nodes[node]['capacity']
                fase = G.nodes[node]['fase']
                # Producción como función seno absoluta
                produccion = abs(np.sin(0.1 * t + fase)) * capacity
                G.nodes[node]['carga_actual'] = produccion
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
                # Distribuir energía alejándose hacia estaciones
                vecinos = list(G.neighbors(node))
                vecinos_estaciones = [n for n in vecinos if G.nodes[n]['tipo'] == 'estacion']
                carga_a_distribuir = G.nodes[node]['carga_actual']
                if vecinos_estaciones:
                    carga_por_estacion = carga_a_distribuir / len(vecinos_estaciones)
                    for estacion in vecinos_estaciones:
                        G.nodes[estacion]['carga_recibida'] += carga_por_estacion
                    G.nodes[node]['carga_actual'] -= carga_a_distribuir

        # Comportamiento de las estaciones
        for node in G.nodes():
            if G.nodes[node]['tipo'] == 'estacion':
                # Aplicar carga recibida
                G.nodes[node]['carga_actual'] += G.nodes[node]['carga_recibida']
                if G.nodes[node]['carga_actual'] > G.nodes[node]['carga_max']:
                    G.nodes[node]['carga_actual'] = G.nodes[node]['carga_max']
                # Calcular cambio de carga basado en función seno
                carga_max = G.nodes[node]['carga_max']
                fase = G.nodes[node]['fase']
                delta_carga = 0.05 * carga_max * np.sin(0.1 * t + fase)
                # Asegurar que delta_carga no exceda +/-5% de carga_max
                delta_carga = max(-0.05 * carga_max, min(0.05 * carga_max, delta_carga))
                # Actualizar carga de la estación
                G.nodes[node]['carga_actual'] += delta_carga
                if G.nodes[node]['carga_actual'] > carga_max:
                    G.nodes[node]['carga_actual'] = carga_max
                elif G.nodes[node]['carga_actual'] < 0:
                    G.nodes[node]['carga_actual'] = 0
                # Registrar el cambio para aplicar al distribuidor en la siguiente unidad de tiempo
                distribuidor = list(G.neighbors(node))[0]  # Estación solo tiene un vecino
                pending_station_changes[distribuidor] = pending_station_changes.get(distribuidor, 0) + delta_carga

        # Aplicar cambios pendientes a distribuidores
        if t in pending_station_changes_timestamps:
            changes = pending_station_changes_timestamps.pop(t)
            for distribuidor, delta in changes.items():
                G.nodes[distribuidor]['carga_actual'] += delta
                if G.nodes[distribuidor]['carga_actual'] > G.nodes[distribuidor]['carga_max']:
                    G.nodes[distribuidor]['carga_actual'] = G.nodes[distribuidor]['carga_max']
                elif G.nodes[distribuidor]['carga_actual'] < 0:
                    G.nodes[distribuidor]['carga_actual'] = 0

        # Programar los cambios pendientes para la siguiente unidad de tiempo
        pending_station_changes_timestamps[t+1] = pending_station_changes
        pending_station_changes = {}

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
    num_nodos = 500  # Número de nodos para pruebas

    G = generar_red(seed, centralizacion, num_nodos)
    G = clasificar_nodos(G)

    # Posiciones de los nodos
    pos = posicionar_nodos(G)

    # Figura de matplotlib
    fig, ax = plt.subplots(figsize=(8,6))
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    # Etiqueta para mostrar el tiempo
    time_label = tk.Label(root, text="Unidad de tiempo: 0\nTiempo transcurrido: 0 s", font=("Arial", 12), anchor='w', justify='left')
    time_label.place(x=10, y=10)

    t = 0  # Tiempo inicial
    dt = 1  # Intervalo de tiempo en segundos (1 unidad de tiempo por segundo)
    start_time = time.time()  # Tiempo de inicio de la simulación

    pending_station_changes = {}  # Cambios de estaciones a aplicar en la siguiente unidad de tiempo
    pending_station_changes_timestamps = {}  # Diccionario con el tiempo como clave

    # Inicializar 'carga_actual' y 'carga_max' para todos los nodos
    for node in G.nodes():
        G.nodes[node]['carga_recibida'] = 0
        if 'carga_actual' not in G.nodes[node]:
            G.nodes[node]['carga_actual'] = 0
        if 'carga_max' not in G.nodes[node]:
            G.nodes[node]['carga_max'] = 100  # Valor por defecto

    # Iniciar la actualización y el dibujo
    actualizar()

    root.mainloop()

except Exception as e:
    print("Ocurrió un error:")
    traceback.print_exc()
    sys.exit(1)
