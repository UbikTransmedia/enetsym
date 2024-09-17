import tkinter as tk
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import random
import time
from matplotlib.colors import Normalize
import matplotlib.cm as cm

try:
    def generar_red(num_nodos, seed):
        random.seed(seed)
        np.random.seed(seed)
        # Generamos un grafo inicial
        G = nx.barabasi_albert_graph(num_nodos, 3, seed=seed)
        return G

    def clasificar_nodos(G):
        num_nodos = G.number_of_nodes()
        degrees = dict(G.degree())
        sorted_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
        
        num_suministradores = max(1, int(0.05 * num_nodos))
        num_estaciones = int(0.60 * num_nodos)
        num_distribuidores = num_nodos - num_suministradores - num_estaciones
        
        # Asignar SUMINISTRADORES (5% de los nodos con más conexiones)
        suministradores = [node for node, deg in sorted_nodes[:num_suministradores]]
        for node in suministradores:
            G.nodes[node]['tipo'] = 'suministrador'
            G.nodes[node]['produccion'] = random.uniform(10, 20)
            G.nodes[node]['fase'] = random.uniform(0, 2*np.pi)
            G.nodes[node]['carga_actual'] = 0
            G.nodes[node]['carga_max'] = G.nodes[node]['produccion']
        
        # Asignar ESTACIONES (60% de los nodos con grado 1)
        estaciones = [node for node, deg in degrees.items() if deg == 1]
        if len(estaciones) < num_estaciones:
            # Necesitamos convertir más nodos en estaciones
            candidatos = [node for node in G.nodes() if node not in suministradores and degrees[node] > 1]
            random.shuffle(candidatos)
            while len(estaciones) < num_estaciones and candidatos:
                nodo = candidatos.pop()
                # Reducir su grado a 1
                vecinos = list(G.neighbors(nodo))
                for vecino in vecinos[1:]:
                    G.remove_edge(nodo, vecino)
                estaciones.append(nodo)
                degrees[nodo] = 1
        
        for node in estaciones:
            G.nodes[node]['tipo'] = 'estacion'
            G.nodes[node]['carga_max'] = random.uniform(50, 100)
            G.nodes[node]['carga_actual'] = 0.5 * G.nodes[node]['carga_max']
            G.nodes[node]['fase'] = random.uniform(0, 2*np.pi)
        
        # Asignar DISTRIBUIDORES al resto de nodos
        distribuidores = [node for node in G.nodes() if 'tipo' not in G.nodes[node]]
        for node in distribuidores:
            G.nodes[node]['tipo'] = 'distribuidor'
            G.nodes[node]['carga_actual'] = 0
            G.nodes[node]['carga_max'] = random.uniform(100, 200)
            G.nodes[node]['energia_recibida'] = 0
            G.nodes[node]['energia_enviada'] = 0
            G.nodes[node]['overloaded'] = False  # Indica si el distribuidor está sobrecargado
        
        return G

    def posicionar_nodos(G):
        # Posicionar los nodos con los SUMINISTRADORES en el centro y las ESTACIONES en la periferia
        suministradores = [node for node, data in G.nodes(data=True) if data['tipo'] == 'suministrador']
        distribuidores = [node for node, data in G.nodes(data=True) if data['tipo'] == 'distribuidor']
        estaciones = [node for node, data in G.nodes(data=True) if data['tipo'] == 'estacion']
        
        layers = [suministradores, distribuidores, estaciones]
        pos = nx.shell_layout(G, nlist=layers)
        return pos

    def dibujar_red():
        ax.clear()
        cargas = []
        cargas_max = []
        node_colors = []
        node_sizes = []
        for node in G.nodes():
            tipo = G.nodes[node]['tipo']
            if tipo == 'suministrador':
                color = 'blue'
                carga_actual = G.nodes[node]['carga_actual']
                carga_max = G.nodes[node]['carga_max']
                carga_relativa = carga_actual / carga_max if carga_max > 0 else 0
                size = (100 + 200 * carga_relativa) * 4  # Tamaño es 4 veces el de los distribuidores
            elif tipo == 'estacion':
                carga_actual = G.nodes[node]['carga_actual']
                carga_max = G.nodes[node]['carga_max']
                carga_relativa = carga_actual / carga_max if carga_max > 0 else 0
                # Color entre negro (0% carga) y azul (100% carga)
                color_intensity = carga_relativa
                color = (0, 0, color_intensity)
                size = 100 + 200 * carga_relativa  # Tamaño depende de la carga
                cargas.append(carga_actual)
                cargas_max.append(carga_max)
            elif tipo == 'distribuidor':
                if G.nodes[node]['overloaded']:
                    color = 'red'
                else:
                    color = 'gray'
                energia_neta = G.nodes[node]['energia_recibida'] - G.nodes[node]['energia_enviada']
                size = 100 + 10 * abs(energia_neta)  # Tamaño depende de la energía neta
            else:
                color = 'gray'
                size = 100
            node_colors.append(color)
            node_sizes.append(size)
        
        nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.3, width=0.5)
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, ax=ax)
        ax.set_axis_off()
        canvas.draw()
        
        # Actualizar estadísticas
        num_estaciones = len([n for n in G.nodes() if G.nodes[n]['tipo'] == 'estacion'])
        estaciones_carga_cero = len([n for n in G.nodes() if G.nodes[n]['tipo'] == 'estacion' and G.nodes[n]['carga_actual'] <= 0])
        estaciones_carga_max = len([n for n in G.nodes() if G.nodes[n]['tipo'] == 'estacion' and G.nodes[n]['carga_actual'] >= G.nodes[n]['carga_max']])
        carga_media_estaciones = sum([G.nodes[n]['carga_actual'] for n in G.nodes() if G.nodes[n]['tipo'] == 'estacion']) / num_estaciones
        produccion_media_suministradores = sum([G.nodes[n]['carga_actual'] for n in G.nodes() if G.nodes[n]['tipo'] == 'suministrador']) / len([n for n in G.nodes() if G.nodes[n]['tipo'] == 'suministrador'])
        
        stats_text = f"Estaciones al 0%: {estaciones_carga_cero}\n"
        stats_text += f"Estaciones al 100%: {estaciones_carga_max}\n"
        stats_text += f"Carga media estaciones: {carga_media_estaciones:.2f}\n"
        stats_text += f"Producción media suministradores: {produccion_media_suministradores:.2f}"
        stats_label.config(text=stats_text)

    def actualizar():
        global t
        t += 1  # Avanza 1 unidad de tiempo en cada iteración
        
        # Reiniciar energía recibida y enviada en distribuidores
        for node in G.nodes():
            if G.nodes[node]['tipo'] == 'distribuidor':
                G.nodes[node]['energia_recibida'] = 0
                G.nodes[node]['energia_enviada'] = 0
                # Si estaba sobrecargado, restablecer
                if G.nodes[node]['overloaded']:
                    G.nodes[node]['overloaded'] = False
                    G.nodes[node]['carga_actual'] = 0
        
        # SUMINISTRADORES generan energía
        for node in G.nodes():
            if G.nodes[node]['tipo'] == 'suministrador':
                produccion_base = G.nodes[node]['produccion']
                fase = G.nodes[node]['fase']
                produccion = abs(np.sin(0.1 * t + fase)) * produccion_base
                G.nodes[node]['carga_actual'] = produccion  # Actualizar carga actual
                vecinos = list(G.neighbors(node))
                if vecinos:
                    carga_por_vecino = produccion / len(vecinos)
                    for vecino in vecinos:
                        if G.nodes[vecino]['tipo'] == 'distribuidor':
                            G.nodes[vecino]['energia_recibida'] += carga_por_vecino
        
        # DISTRIBUIDORES reciben y envían energía
        for node in G.nodes():
            if G.nodes[node]['tipo'] == 'distribuidor' and not G.nodes[node]['overloaded']:
                # Recibir energía de suministradores y estaciones
                energia_recibida = G.nodes[node]['energia_recibida']
                vecinos = list(G.neighbors(node))
                estaciones_vecinas = [n for n in vecinos if G.nodes[n]['tipo'] == 'estacion']
                for estacion in estaciones_vecinas:
                    if G.nodes[estacion]['carga_actual'] >= G.nodes[estacion]['carga_max']:
                        # Absorber energía de la estación
                        delta = min(5, G.nodes[estacion]['carga_actual'])
                        G.nodes[estacion]['carga_actual'] -= delta
                        energia_recibida += delta
                G.nodes[node]['carga_actual'] += energia_recibida
                
                # Verificar si excede su carga máxima
                if G.nodes[node]['carga_actual'] >= G.nodes[node]['carga_max']:
                    G.nodes[node]['overloaded'] = True  # Marcar como sobrecargado
                    G.nodes[node]['carga_actual'] = G.nodes[node]['carga_max']
                else:
                    # Enviar energía a estaciones que no están al 100%
                    energia_disponible = G.nodes[node]['carga_actual']
                    estaciones_para_enviar = [n for n in estaciones_vecinas if G.nodes[n]['carga_actual'] < G.nodes[n]['carga_max']]
                    if estaciones_para_enviar:
                        carga_por_estacion = energia_disponible / len(estaciones_para_enviar)
                        for estacion in estaciones_para_enviar:
                            G.nodes[estacion]['carga_actual'] += carga_por_estacion
                            G.nodes[node]['energia_enviada'] += carga_por_estacion
                            if G.nodes[estacion]['carga_actual'] > G.nodes[estacion]['carga_max']:
                                G.nodes[estacion]['carga_actual'] = G.nodes[estacion]['carga_max']
                        G.nodes[node]['carga_actual'] -= G.nodes[node]['energia_enviada']
                        if G.nodes[node]['carga_actual'] < 0:
                            G.nodes[node]['carga_actual'] = 0
        
        # ESTACIONES consumen o producen energía
        for node in G.nodes():
            if G.nodes[node]['tipo'] == 'estacion':
                fase = G.nodes[node]['fase']
                carga_max = G.nodes[node]['carga_max']
                delta_carga = 0.05 * carga_max * np.sin(0.1 * t + fase)
                delta_carga = max(-0.05 * carga_max, min(0.05 * carga_max, delta_carga))
                G.nodes[node]['carga_actual'] += delta_carga
                if G.nodes[node]['carga_actual'] > carga_max:
                    G.nodes[node]['carga_actual'] = carga_max
                elif G.nodes[node]['carga_actual'] < 0:
                    G.nodes[node]['carga_actual'] = 0
        
        # Actualizar el tiempo en la etiqueta
        elapsed_time = time.time() - start_time
        time_label.config(text=f"Unidad de tiempo: {t}\nTiempo transcurrido: {elapsed_time:.2f} s")
        
        # Dibujar la red y actualizar estadísticas
        dibujar_red()
        
        # Programar la siguiente actualización
        root.after(int(dt * 1000), actualizar)

    # Configuración de la ventana principal
    root = tk.Tk()
    root.geometry("1080x780")
    root.title("Red de Nodos")

    # Generar la red
    seed = 42
    num_nodos = 800  # 800 nodos
    G = generar_red(num_nodos, seed)
    G = clasificar_nodos(G)
    pos = posicionar_nodos(G)

    # Figura de matplotlib
    fig, ax = plt.subplots(figsize=(8,6))
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    # Etiquetas para mostrar el tiempo y estadísticas
    time_label = tk.Label(root, text="Unidad de tiempo: 0", font=("Arial", 12), anchor='w', justify='left')
    time_label.place(x=10, y=10)
    stats_label = tk.Label(root, text="", font=("Arial", 12), anchor='w', justify='left')
    stats_label.place(x=10, y=50)

    t = 0  # Tiempo inicial
    dt = 0.1  # Intervalo de tiempo en segundos (10 unidades de tiempo por segundo)
    start_time = time.time()  # Tiempo de inicio de la simulación

    # Iniciar la actualización y el dibujo
    actualizar()
    root.mainloop()

except Exception as e:
    print("Ocurrió un error:")
    print(e)
