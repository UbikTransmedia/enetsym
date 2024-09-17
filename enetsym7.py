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
                G.nodes[node]['produccion'] = random.uniform(5, 10)
                G.nodes[node]['fase'] = random.uniform(0, 2*np.pi)
                G.nodes[node]['carga_actual'] = 0
                G.nodes[node]['carga_max'] = G.nodes[node]['produccion']  # Establecer carga_max
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
            G.nodes[node]['carga_max'] = 1  # Establecer carga_max finito
            # Conectar a varios nodos aleatorios
            num_conexiones = random.randint(5, 15)
            nodos_a_conectar = random.sample(nodos_disponibles, num_conexiones)
            for n in nodos_a_conectar:
                if not G.has_edge(node, n):
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
            if G.nodes[node]['tipo'] != 'controlador':
                cargas.append(G.nodes[node].get('carga_actual', 0))
                cargas_max.append(G.nodes[node].get('carga_max', 1))
        cargas_relativas = [c / m if m != 0 else 0 for c, m in zip(cargas, cargas_max)]

        norm = Normalize(vmin=0, vmax=1)
        cmap = cm.get_cmap('YlOrRd')  # Colormap de amarillo a rojo

        node_colors = []
        node_sizes = []
        for node in G.nodes():
            tipo = G.nodes[node]['tipo']
            if tipo == 'controlador':
                node_colors.append('purple')
                node_sizes.append(300)
            else:
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

    def restar_carga(nodo, consumo, visitados):
        if nodo in visitados:
            return
        visitados.add(nodo)
        tipo = G.nodes[nodo]['tipo']
        if tipo == 'suministrador' or tipo == 'controlador':
            return
        else:
            carga_actual = G.nodes[nodo]['carga_actual']
            if carga_actual >= consumo:
                G.nodes[nodo]['carga_actual'] -= consumo
            else:
                deficit = consumo - carga_actual
                G.nodes[nodo]['carga_actual'] = 0
                vecinos = list(G.neighbors(nodo))
                vecinos = [n for n in vecinos if G.nodes[n]['tipo'] not in ['consumidor', 'controlador'] and n not in visitados]
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
                # Actualizar carga_actual del suministrador
                G.nodes[node]['carga_actual'] = produccion
                vecinos = list(G.neighbors(node))
                if vecinos:
                    carga_por_vecino = produccion / len(vecinos)
                    for vecino in vecinos:
                        if G.nodes[vecino]['tipo'] not in ['suministrador', 'controlador']:
                            G.nodes[vecino]['carga_recibida'] += carga_por_vecino

        # Actualización de distribuidores
        for node in G.nodes():
            if G.nodes[node]['tipo'] == 'distribuidor':
                G.nodes[node]['carga_actual'] += G.nodes[node]['carga_recibida']
                if G.nodes[node]['carga_actual'] > G.nodes[node]['carga_max']:
                    G.nodes[node]['carga_actual'] = G.nodes[node]['carga_max']
                # Distribuir un porcentaje de la carga
                G.nodes[node]['carga_a_distribuir'] = G.nodes[node]['carga_actual'] * 0.9
                # Mantener una parte de la carga
                G.nodes[node]['carga_actual'] -= G.nodes[node]['carga_a_distribuir']

        # Distribución de carga de los distribuidores
        for node in G.nodes():
            if G.nodes[node]['tipo'] == 'distribuidor':
                carga_a_distribuir = G.nodes[node]['carga_a_distribuir']
                vecinos = list(G.neighbors(node))
                vecinos = [n for n in vecinos if G.nodes[n]['tipo'] not in ['suministrador', 'controlador']]
                if vecinos:
                    carga_por_vecino = carga_a_distribuir / len(vecinos)
                    for vecino in vecinos:
                        G.nodes[vecino]['carga_recibida'] += carga_por_vecino
                G.nodes[node]['carga_a_distribuir'] = 0

        # Actualización de estaciones y consumidores
        for node in G.nodes():
            if G.nodes[node]['tipo'] in ['estacion', 'consumidor']:
                G.nodes[node]['carga_actual'] += G.nodes[node]['carga_recibida']
                if G.nodes[node]['carga_actual'] > G.nodes[node]['carga_max']:
                    G.nodes[node]['carga_actual'] = G.nodes[node]['carga_max']

        # Consumo de los consumidores
        for node in G.nodes():
            if G.nodes[node]['tipo'] == 'consumidor':
                consumo = G.nodes[node]['consumo']
                if G.nodes[node]['carga_actual'] >= consumo:
                    G.nodes[node]['carga_actual'] -= consumo
                else:
                    deficit = consumo - G.nodes[node]['carga_actual']
                    G.nodes[node]['carga_actual'] = 0
                    vecinos = list(G.neighbors(node))
                    if vecinos:
                        distribuidor = vecinos[0]
                        restar_carga(distribuidor, deficit, set([node]))

        # Acción de los controladores
        for node in G.nodes():
            if G.nodes[node]['tipo'] == 'controlador':
                vecinos = list(G.neighbors(node))
                for vecino in vecinos:
                    carga_actual = G.nodes[vecino]['carga_actual']
                    carga_max = G.nodes[vecino]['carga_max']
                    if carga_actual >= carga_max:
                        G.nodes[vecino]['carga_actual'] = 0  # Reiniciar la carga

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
    G = convertir_estaciones_en_consumidores(G)
    G = agregar_controladores(G)

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

    # Inicializar 'carga_a_distribuir' y 'carga_actual' para todos los nodos
    for node in G.nodes():
        G.nodes[node]['carga_recibida'] = 0
        G.nodes[node]['carga_a_distribuir'] = 0
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
