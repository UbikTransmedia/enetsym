import tkinter as tk
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import random
import time

try:
    def generar_red(num_nodos):
        # Generamos un grafo inicial sin semilla fija
        G = nx.barabasi_albert_graph(num_nodos, 3)
        return G

    def clasificar_nodos(G):
        num_nodos = G.number_of_nodes()
        degrees = dict(G.degree())
        sorted_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
        
        num_suministradores = max(1, int(0.05 * num_nodos))
        num_estaciones = int(0.60 * num_nodos)
        num_distribuidores = num_nodos - num_suministradores - num_estaciones
        
        # Definir tipos de energía y sus variaciones
        tipos_energia = ['EÓLICA', 'GEOTÉRMICA', 'NUCLEAR', 'OCEÁNICA', 'HIDROELÉCTRICA', 'BIOMASA']
        
        # Asignar SUMINISTRADORES
        suministradores = [node for node, deg in sorted_nodes[:num_suministradores]]
        
        # Asegurar que solo hay un suministrador de tipo SOLAR
        nodo_solar = suministradores[0]
        G.nodes[nodo_solar]['tipo'] = 'suministrador'
        G.nodes[nodo_solar]['energy_type'] = 'SOLAR'
        G.nodes[nodo_solar]['produccion'] = random.uniform(10, 20)
        G.nodes[nodo_solar]['fase'] = 0  # Fase cero para sincronizar con las 06:00
        G.nodes[nodo_solar]['carga_actual'] = 0
        G.nodes[nodo_solar]['carga_max'] = G.nodes[nodo_solar]['produccion']
        G.nodes[nodo_solar]['produccion_anterior'] = 0  # Para determinar si la producción sube o baja
        
        # Asignar tipos de energía a los demás suministradores
        otros_suministradores = suministradores[1:]
        tipos_asignados = random.choices(tipos_energia, k=len(otros_suministradores))
        
        for node, energy_type in zip(otros_suministradores, tipos_asignados):
            G.nodes[node]['tipo'] = 'suministrador'
            G.nodes[node]['energy_type'] = energy_type
            G.nodes[node]['produccion'] = random.uniform(10, 20)
            G.nodes[node]['fase'] = random.uniform(0, 2*np.pi)
            G.nodes[node]['carga_actual'] = 0
            G.nodes[node]['carga_max'] = G.nodes[node]['produccion']
            G.nodes[node]['produccion_anterior'] = 0  # Para determinar si la producción sube o baja
        
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
            G.nodes[node]['carga_anterior'] = G.nodes[node]['carga_actual']  # Para determinar si ganó o perdió carga
        
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
        
        # Ajustar las posiciones para aprovechar el 95% del ancho
        for node in pos:
            x, y = pos[node]
            pos[node] = (x * 1.9, y)  # Multiplicar x para ensanchar (1.9 es aproximadamente 95% del ancho)
        return pos

    def calcular_produccion(t, energy_type, produccion_base, fase):
        if energy_type == 'EÓLICA':
            # Energía eólica varía rápidamente
            produccion = abs(np.sin(0.2 * t + fase)) * produccion_base
        elif energy_type == 'SOLAR':
            # Energía solar varía con el ciclo del día (06:00 a 18:00)
            hora = (t % 24)
            if 6 <= hora <= 18:
                angulo = ((hora - 6) / 12) * np.pi  # De 0 a π
                produccion = np.sin(angulo) * produccion_base
            else:
                produccion = 0
        elif energy_type == 'GEOTÉRMICA':
            # Energía geotérmica es estable
            produccion = produccion_base * 0.9 + 0.1 * produccion_base * np.sin(0.05 * t + fase)
        elif energy_type == 'NUCLEAR':
            # Energía nuclear es muy estable
            produccion = produccion_base
        elif energy_type == 'OCEÁNICA':
            # Energía oceánica varía con las mareas
            produccion = abs(np.sin(0.05 * t + fase)) * produccion_base
        elif energy_type == 'HIDROELÉCTRICA':
            # Energía hidroeléctrica es relativamente estable
            produccion = produccion_base * 0.8 + 0.2 * produccion_base * np.sin(0.05 * t + fase)
        elif energy_type == 'BIOMASA':
            # Biomasa es estable
            produccion = produccion_base * 0.95 + 0.05 * produccion_base * np.sin(0.02 * t + fase)
        else:
            produccion = produccion_base
        return produccion

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
                carga_actual = G.nodes[node]['carga_actual']
                carga_max = G.nodes[node]['carga_max']
                carga_relativa = carga_actual / carga_max if carga_max > 0 else 0
                # Tamaño del nodo basado en la altura de la etiqueta (dos líneas, fuente tamaño 16)
                # Aproximadamente 16 puntos por línea, total 32 puntos de altura
                # Radio entre 32 y 64 puntos
                radius = 32 + carga_relativa * (64 - 32)
                size = radius ** 2  # node_size es proporcional al área
                # Color entre gris (bajo) y amarillo (alto)
                color_intensity = carga_relativa
                color = (color_intensity, color_intensity, 0)
                # Etiqueta de producción con tipo de energía
                produccion_actual = G.nodes[node]['carga_actual']
                produccion_anterior = G.nodes[node]['produccion_anterior']
                color_texto = 'green' if produccion_actual >= produccion_anterior else 'red'
                energy_type = G.nodes[node]['energy_type']
                labels[node] = f"{energy_type}\n{produccion_actual:.1f}"
                # Dibujar etiqueta con tamaño de fuente aumentado
                nx.draw_networkx_labels(
                    G, pos, labels={node: labels[node]},
                    font_color=color_texto, font_size=16, font_weight='bold',
                    ax=ax1,
                    bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.2')
                )
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
                # Etiqueta de carga
                delta_carga = carga_actual - carga_anterior
                color_texto = 'green' if delta_carga >= 0 else 'red'
                labels[node] = f"{carga_actual:.1f}"
                # Dibujar etiqueta con negrita y borde
                nx.draw_networkx_labels(
                    G, pos, labels={node: labels[node]},
                    font_color=color_texto, font_size=8, font_weight='bold',
                    ax=ax1,
                    bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.2')
                )
            elif tipo == 'distribuidor':
                carga_actual = G.nodes[node]['carga_actual']
                carga_max = G.nodes[node]['carga_max']
                carga_relativa = carga_actual / carga_max if carga_max > 0 else 0
                # Tamaño depende de la carga
                size = (100 + 200 * carga_relativa) * 3
                # Color que varía de gris a naranja
                color_low = (0.5, 0.5, 0.5)  # Gris
                color_high = (1.0, 0.5, 0.0)  # Naranja
                color = tuple(color_low[i] + carga_relativa * (color_high[i] - color_low[i]) for i in range(3))
                # Etiqueta de porcentaje de carga con símbolo %
                porcentaje_carga = (carga_actual / carga_max) * 100 if carga_max > 0 else 0
                labels[node] = f"{porcentaje_carga:.1f}%"
                # Dibujar etiqueta con negrita y borde
                nx.draw_networkx_labels(
                    G, pos, labels={node: labels[node]},
                    font_color='black', font_size=8, font_weight='bold',
                    ax=ax1,
                    bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.2')
                )
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
        
        # Calcular nuevas estadísticas
        total_energia_acumulada = sum([G.nodes[n]['carga_actual'] for n in G.nodes()])
        total_carga_actual = sum([G.nodes[n]['carga_actual'] for n in G.nodes()])
        total_carga_max = sum([G.nodes[n]['carga_max'] for n in G.nodes()])
        porcentaje_total_carga = (total_carga_actual / total_carga_max) * 100 if total_carga_max > 0 else 0
        porcentaje_carga_libre = ((total_carga_max - total_carga_actual) / total_carga_max) * 100 if total_carga_max > 0 else 0
        
        # Actualizar series de tiempo
        tiempos.append(t)
        serie_estaciones_cero.append(estaciones_carga_cero)
        serie_estaciones_max.append(estaciones_carga_max)
        serie_carga_media_estaciones.append(carga_media_estaciones)
        serie_produccion_media_suministradores.append(produccion_media_suministradores)
        serie_distribuidores_sobrecargados.append(distribuidores_sobrecargados)
        serie_total_energia_acumulada.append(total_energia_acumulada)
        serie_porcentaje_total_carga.append(porcentaje_total_carga)
        serie_porcentaje_carga_libre.append(porcentaje_carga_libre)
        
        # Dibujar las series en el gráfico inferior
        ax2.clear()
        ax2_right.clear()
        ax2.set_facecolor('none')
        ax2_right.set_facecolor('none')
        
        ax2.plot(tiempos, serie_estaciones_cero, color='green', label='Estaciones al 0%')
        ax2.plot(tiempos, serie_estaciones_max, color='blue', label='Estaciones al 100%')
        ax2.plot(tiempos, serie_carga_media_estaciones, color='orange', label='Carga media estaciones')
        ax2.plot(tiempos, serie_produccion_media_suministradores, color='purple', label='Producción media suministradores')
        ax2.plot(tiempos, serie_distribuidores_sobrecargados, color='red', label='Distribuidores sobrecargados')
        ax2.plot(tiempos, serie_porcentaje_total_carga, color='cyan', label='Porcentaje total de carga')
        # Nueva serie de porcentaje de carga libre
        ax2.plot(tiempos, serie_porcentaje_carga_libre, color='black', linestyle='dotted', linewidth=2, label='Porcentaje carga libre')
        
        # Nueva serie en el eje Y derecho
        ax2_right.plot(tiempos, serie_total_energia_acumulada, color='magenta', label='Total energía acumulada')
        
        # Mostrar el último valor de cada serie sobre el último punto
        if tiempos:
            last_time = tiempos[-1]
            ax2.text(last_time, serie_estaciones_cero[-1], f'{serie_estaciones_cero[-1]}', color='green')
            ax2.text(last_time, serie_estaciones_max[-1], f'{serie_estaciones_max[-1]}', color='blue')
            ax2.text(last_time, serie_carga_media_estaciones[-1], f'{serie_carga_media_estaciones[-1]:.2f}', color='orange')
            ax2.text(last_time, serie_produccion_media_suministradores[-1], f'{serie_produccion_media_suministradores[-1]:.2f}', color='purple')
            ax2.text(last_time, serie_distribuidores_sobrecargados[-1], f'{serie_distribuidores_sobrecargados[-1]}', color='red')
            ax2.text(last_time, serie_porcentaje_total_carga[-1], f'{serie_porcentaje_total_carga[-1]:.1f}%', color='cyan')
            ax2.text(last_time, serie_porcentaje_carga_libre[-1], f'{serie_porcentaje_carga_libre[-1]:.1f}%', color='black')
            ax2_right.text(last_time, serie_total_energia_acumulada[-1], f'{serie_total_energia_acumulada[-1]:.1f}', color='magenta')
        
        # Leyendas y etiquetas
        ax2.set_xlabel('Tiempo')
        ax2.set_ylabel('Valores')
        ax2_right.set_ylabel('Energía Acumulada')
        ax2.legend(loc='upper left')
        ax2_right.legend(loc='upper right')
        
        ax2.grid(True)
        
        # Ajustar límites del gráfico
        ax2.relim()
        ax2.autoscale_view()
        ax2_right.relim()
        ax2_right.autoscale_view()
        
        # Ajustar márgenes y espacios
        plt.subplots_adjust(left=0.15, right=0.85, top=0.95, bottom=0.05, hspace=0.1)
        
        # Actualizar los dibujos
        canvas.draw()
        
        # Actualizar el tiempo en la etiqueta
        elapsed_time = time.time() - start_time
        
        # Contar los nodos de cada tipo
        num_suministradores = len([n for n in G.nodes() if G.nodes[n]['tipo'] == 'suministrador'])
        num_distribuidores = len([n for n in G.nodes() if G.nodes[n]['tipo'] == 'distribuidor'])
        num_estaciones = len([n for n in G.nodes() if G.nodes[n]['tipo'] == 'estacion'])
        
        time_label.config(text=f"Unidad de tiempo: {t}\nTiempo transcurrido: {elapsed_time:.2f} s\nNodos: {G.number_of_nodes()}\nSuministradores: {num_suministradores}\nDistribuidores: {num_distribuidores}\nEstaciones: {num_estaciones}")
        
        # Calcular la hora del día usando t
        hora_del_dia = t % 24
        hora_del_dia_formato = f"Hora: {int(hora_del_dia):02d}:{int((hora_del_dia % 1)*60):02d}"
        # Actualizar la etiqueta de la hora
        time_of_day_label.config(text=hora_del_dia_formato)
        
        # -------------------
        # Gráfico de barras a la derecha: Carga total actual de distribuidores y estaciones
        ax3.clear()
        total_carga_distribuidores = sum([G.nodes[n]['carga_actual'] for n in G.nodes() if G.nodes[n]['tipo'] == 'distribuidor'])
        total_carga_estaciones = sum([G.nodes[n]['carga_actual'] for n in G.nodes() if G.nodes[n]['tipo'] == 'estacion'])
        
        labels_derecha = ['Distribuidores', 'Estaciones']
        valores_derecha = [total_carga_distribuidores, total_carga_estaciones]
        colores_derecha = ['orange', 'blue']
        
        ax3.bar(labels_derecha, valores_derecha, color=colores_derecha)
        ax3.set_title('Carga Total Actual')
        ax3.set_ylabel('Energía')
        ax3.set_xticks(range(len(labels_derecha)))
        ax3.set_xticklabels(labels_derecha, rotation=45, ha='right')
        
        # Gráfico de barras a la izquierda: Mix energético
        ax4.clear()
        tipos_suministradores = list(set([G.nodes[n]['energy_type'] for n in G.nodes() if G.nodes[n]['tipo'] == 'suministrador']))
        produccion_por_tipo = {}
        for tipo in tipos_suministradores:
            produccion_por_tipo[tipo] = sum([G.nodes[n]['carga_actual'] for n in G.nodes() if G.nodes[n]['tipo'] == 'suministrador' and G.nodes[n]['energy_type'] == tipo])
        
        labels_izquierda = list(produccion_por_tipo.keys())
        valores_izquierda = list(produccion_por_tipo.values())
        
        ax4.bar(labels_izquierda, valores_izquierda)
        ax4.set_title('Mix Energético')
        ax4.set_ylabel('Producción')
        ax4.set_xticks(range(len(labels_izquierda)))
        ax4.set_xticklabels(labels_izquierda, rotation=45, ha='right')
        
        # Actualizar los dibujos nuevamente
        canvas.draw()

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
                G.nodes[node]['produccion_anterior'] = G.nodes[node]['carga_actual']
                produccion_base = G.nodes[node]['produccion']
                fase = G.nodes[node]['fase']
                energy_type = G.nodes[node]['energy_type']
                produccion = calcular_produccion(t, energy_type, produccion_base, fase)
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
                        G.nodes[estacion]['carga_anterior'] = G.nodes[estacion]['carga_actual']
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
                            G.nodes[estacion]['carga_anterior'] = G.nodes[estacion]['carga_actual']
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
                G.nodes[node]['carga_anterior'] = G.nodes[node]['carga_actual']
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
    root.geometry("1200x780")  # Aumenté el ancho para acomodar los nuevos gráficos
    root.title("Red de Nodos")

    # Generar la red
    num_nodos = 200  # 200 nodos
    G = generar_red(num_nodos)
    G = clasificar_nodos(G)
    pos = posicionar_nodos(G)

    # Listas para las series de tiempo
    tiempos = []
    serie_estaciones_cero = []
    serie_estaciones_max = []
    serie_carga_media_estaciones = []
    serie_produccion_media_suministradores = []
    serie_distribuidores_sobrecargados = []
    serie_total_energia_acumulada = []
    serie_porcentaje_total_carga = []
    serie_porcentaje_carga_libre = []

    # Figura de matplotlib
    fig = plt.Figure(figsize=(10, 6))  # Aumenté el ancho de la figura
    fig.patch.set_facecolor('white')

    # Dividir la figura en varios ejes
    ax1 = fig.add_axes([0.15, 0.35, 0.7, 0.6])  # Grafo de nodos
    ax2 = fig.add_axes([0.15, 0.05, 0.7, 0.25], facecolor='none')  # Gráfico inferior
    ax2_right = ax2.twinx()
    ax3 = fig.add_axes([0.88, 0.35, 0.1, 0.6])  # Gráfico de barras a la derecha
    ax4 = fig.add_axes([0.02, 0.35, 0.1, 0.6])  # Gráfico de barras a la izquierda

    # Añadir el canvas de matplotlib al widget de Tkinter
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    # Etiqueta para mostrar el tiempo (alineado a la izquierda y tamaño reducido)
    time_label = tk.Label(root, text="", font=("Arial", 12), anchor='w', justify='left')
    time_label.place(x=10, y=10)

    # Etiqueta para mostrar la hora del día (tamaño doble)
    time_of_day_label = tk.Label(root, text="Hora: 00:00", font=("Arial", 24), anchor='e', justify='right')
    time_of_day_label.place(relx=1.0, x=-10, y=10, anchor='ne')

    t = 0  # Tiempo inicial
    dt = 0.045  # Intervalo de tiempo en segundos

    start_time = time.time()  # Tiempo de inicio de la simulación

    # Iniciar la actualización y el dibujo
    actualizar()
    root.mainloop()

except Exception as e:
    print("Ocurrió un error:")
    print(e)
