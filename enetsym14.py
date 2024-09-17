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
            G.nodes[node]['produccion_anterior'] = 0  # Para seguimiento de producción
            
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
            G.nodes[node]['carga_anterior'] = G.nodes[node]['carga_actual']  # Para seguimiento de carga
        
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
        ax1.clear()
        cargas = []
        cargas_max = []
        node_colors = []
        node_sizes = []
        labels = {}
        for node in G.nodes():
            tipo = G.nodes[node]['tipo']
            if tipo == 'suministrador':
                color = 'blue'
                carga_actual = G.nodes[node]['carga_actual']
                carga_max = G.nodes[node]['carga_max']
                carga_relativa = carga_actual / carga_max if carga_max > 0 else 0
                size = (100 + 200 * carga_relativa) * 4  # Tamaño es 4 veces el de los distribuidores
                
                # Texto sobre el nodo
                produccion_actual = carga_actual
                produccion_anterior = G.nodes[node]['produccion_anterior']
                if produccion_actual > produccion_anterior:
                    color_text = 'green'
                else:
                    color_text = 'red'
                labels[node] = f"{produccion_actual:.1f}"
                nx.draw_networkx_labels(G, pos, labels={node: labels[node]}, font_color=color_text, font_size=8, ax=ax1)
            elif tipo == 'estacion':
                carga_anterior = G.nodes[node]['carga_anterior']
                carga_actual = G.nodes[node]['carga_actual']
                carga_max = G.nodes[node]['carga_max']
                carga_relativa = carga_actual / carga_max if carga_max > 0 else 0
                # Color entre negro (0% carga) y azul (100% carga)
                color_intensity = carga_relativa
                color = (0, 0, color_intensity)
                size = 100 + 200 * carga_relativa  # Tamaño depende de la carga
                cargas.append(carga_actual)
                cargas_max.append(carga_max)
                
                # Texto sobre el nodo
                if carga_actual > carga_anterior:
                    color_text = 'green'
                else:
                    color_text = 'red'
                labels[node] = f"{carga_actual:.1f}"
                nx.draw_networkx_labels(G, pos, labels={node: labels[node]}, font_color=color_text, font_size=8, ax=ax1)
            elif tipo == 'distribuidor':
                if G.nodes[node]['overloaded']:
                    color = 'red'
                else:
                    color = 'gray'
                energia_neta = G.nodes[node]['energia_recibida'] - G.nodes[node]['energia_enviada']
                size = 100 + 10 * abs(energia_neta)  # Tamaño depende de la energía neta
                
                # Texto sobre el nodo
                carga_actual = G.nodes[node]['carga_actual']
                carga_max = G.nodes[node]['carga_max']
                porcentaje_carga = (carga_actual / carga_max) * 100 if carga_max > 0 else 0
                labels[node] = f"{porcentaje_carga:.1f}%"
                nx.draw_networkx_labels(G, pos, labels={node: labels[node]}, font_color='black', font_size=8, ax=ax1)
            else:
                color = 'gray'
                size = 100
            node_colors.append(color)
            node_sizes.append(size)
        
        nx.draw_networkx_edges(G, pos, ax=ax1, alpha=0.3, width=0.5)
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, ax=ax1)
        ax1.set_axis_off()
        
        # Actualizar estadísticas
        num_estaciones = len([n for n in G.nodes() if G.nodes[n]['tipo'] == 'estacion'])
        estaciones_carga_cero = len([n for n in G.nodes() if G.nodes[n]['tipo'] == 'estacion' and G.nodes[n]['carga_actual'] <= 0])
        estaciones_carga_max = len([n for n in G.nodes() if G.nodes[n]['tipo'] == 'estacion' and G.nodes[n]['carga_actual'] >= G.nodes[n]['carga_max']])
        carga_media_estaciones = sum([G.nodes[n]['carga_actual'] for n in G.nodes() if G.nodes[n]['tipo'] == 'estacion']) / num_estaciones
        produccion_media_suministradores = sum([G.nodes[n]['carga_actual'] for n in G.nodes() if G.nodes[n]['tipo'] == 'suministrador']) / len([n for n in G.nodes() if G.nodes[n]['tipo'] == 'suministrador'])
        distribuidores_sobrecargados = len([n for n in G.nodes() if G.nodes[n]['tipo'] == 'distribuidor' and G.nodes[n]['overloaded']])
        
        # Actualizar series de tiempo
        tiempos.append(t)
        serie_estaciones_cero.append(estaciones_carga_cero)
        serie_estaciones_max.append(estaciones_carga_max)
        serie_carga_media_estaciones.append(carga_media_estaciones)
        serie_produccion_media_suministradores.append(produccion_media_suministradores)
        serie_distribuidores_sobrecargados.append(distribuidores_sobrecargados)
        
        # Dibujar las series en el gráfico inferior
        ax2.clear()
        ax2.set_facecolor('none')
        ax2.plot(tiempos, serie_estaciones_cero, color='green', label='Estaciones al 0%')
        ax2.plot(tiempos, serie_estaciones_max, color='blue', label='Estaciones al 100%')
        ax2.plot(tiempos, serie_carga_media_estaciones, color='orange', label='Carga media estaciones')
        ax2.plot(tiempos, serie_produccion_media_suministradores, color='purple', label='Producción media suministradores')
        ax2.plot(tiempos, serie_distribuidores_sobrecargados, color='red', label='Distribuidores sobrecargados')
        
        # Mostrar el último valor de cada serie sobre el último punto
        if tiempos:
            last_time = tiempos[-1]
            ax2.text(last_time, serie_estaciones_cero[-1], f'{serie_estaciones_cero[-1]}', color='green')
            ax2.text(last_time, serie_estaciones_max[-1], f'{serie_estaciones_max[-1]}', color='blue')
            ax2.text(last_time, serie_carga_media_estaciones[-1], f'{serie_carga_media_estaciones[-1]:.2f}', color='orange')
            ax2.text(last_time, serie_produccion_media_suministradores[-1], f'{serie_produccion_media_suministradores[-1]:.2f}', color='purple')
            ax2.text(last_time, serie_distribuidores_sobrecargados[-1], f'{serie_distribuidores_sobrecargados[-1]}', color='red')
        
        # Añadir etiquetas de unidades en el eje Y
        ax2.set_yticks(sorted(set(serie_estaciones_cero + serie_estaciones_max + serie_distribuidores_sobrecargados)))
        ax2.set_yticklabels(ax2.get_yticks())
        
        # Añadir leyenda con unidades
        ax2.legend(loc='upper left')
        ax2.set_xlabel('Tiempo')
        ax2.set_ylabel('Valores')
        ax2.grid(True)
        
        # Ajustar límites del gráfico
        ax2.relim()
        ax2.autoscale_view()
        
        # Actualizar los dibujos
        canvas.draw()
        
        # Actualizar el tiempo en la etiqueta
        elapsed_time = time.time() - start_time
        time_label.config(text=f"Unidad de tiempo: {t}\nTiempo transcurrido: {elapsed_time:.2f} s")

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
        
        # Guardar producción anterior de suministradores
        for node in G.nodes():
            if G.nodes[node]['tipo'] == 'suministrador':
                G.nodes[node]['produccion_anterior'] = G.nodes[node]['carga_actual']
        
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
        
        # Guardar carga anterior de estaciones
        for node in G.nodes():
            if G.nodes[node]['tipo'] == 'estacion':
                G.nodes[node]['carga_anterior'] = G.nodes[node]['carga_actual']
        
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
    num_nodos = 200  # 200 nodos
    G = generar_red(num_nodos, seed)
    G = clasificar_nodos(G)
    pos = posicionar_nodos(G)

    # Listas para las series de tiempo
    tiempos = []
    serie_estaciones_cero = []
    serie_estaciones_max = []
    serie_carga_media_estaciones = []
    serie_produccion_media_suministradores = []
    serie_distribuidores_sobrecargados = []

    # Figura de matplotlib
    fig = plt.Figure(figsize=(8, 6))
    fig.patch.set_facecolor('white')

    # Dividir la figura en dos ejes
    ax1 = fig.add_axes([0.05, 0.35, 0.9, 0.6])  # [left, bottom, width, height]
    ax2 = fig.add_axes([0.05, 0.05, 0.9, 0.25], facecolor='none')

    # Añadir el canvas de matplotlib al widget de Tkinter
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    # Etiqueta para mostrar el tiempo
    time_label = tk.Label(root, text="Unidad de tiempo: 0", font=("Arial", 12), anchor='w', justify='left')
    time_label.place(x=10, y=10)

    t = 0  # Tiempo inicial
    dt = 0.045  # Intervalo de tiempo en segundos
    start_time = time.time()  # Tiempo de inicio de la simulación

    # Iniciar la actualización y el dibujo
    actualizar()
    root.mainloop()

except Exception as e:
    print("Ocurrió un error:")
    print(e)
