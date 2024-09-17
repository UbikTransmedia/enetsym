# Simulación de Red de Energía

Este proyecto simula una red de nodos interconectados que representan diferentes tipos de entidades dentro de un sistema energético: suministradores, distribuidores y estaciones. Utilizando el framework de `NetworkX` para modelar grafos y `Tkinter` para la interfaz gráfica, la simulación muestra cómo fluye la energía entre los diferentes nodos y las estadísticas relacionadas a la producción y consumo de energía.

## Funcionalidades

- **Generación de red**: Se genera un grafo tipo Barabási-Albert con 250 nodos, que luego se clasifican en tres tipos:
  - **Suministradores**: Generan energía con diferentes fuentes (Solar, Eólica, Geotérmica, etc.).
  - **Distribuidores**: Intermedian el flujo de energía entre suministradores y estaciones.
  - **Estaciones**: Consumen o almacenan energía, simulando estaciones de carga.

- **Flujo de energía**: A lo largo del tiempo, los suministradores generan energía que es distribuida por los distribuidores a las estaciones. La cantidad de energía generada y distribuida cambia dinámicamente según el tipo de energía y las características de cada nodo.

- **Actualización visual**: La red se actualiza visualmente en tiempo real, mostrando:
  - **Tamaños de nodo**: Basados en la cantidad de energía que contienen.
  - **Colores**: Representan el nivel de carga (amarillo para suministradores, azul para estaciones, naranja para distribuidores).
  - **Gráficos adicionales**:
    - **Gráfico de barras**: Carga total en distribuidores y estaciones, además de la capacidad libre.
    - **Mix energético**: Producción total por cada tipo de energía.

## Reglas y comportamiento de los nodos

1. **Suministradores**:
   - Generan energía según su tipo (Solar, Eólica, Nuclear, etc.).
   - La energía se produce siguiendo una serie de funciones temporales que varían según el tipo de energía. Por ejemplo, la energía solar depende de la hora del día, mientras que la eólica varía rápidamente.

2. **Distribuidores**:
   - Reciben energía de los suministradores y la envían a las estaciones. Si reciben demasiada energía, pueden sobrecargarse y detener el envío de energía.

3. **Estaciones**:
   - Pueden almacenar energía hasta una capacidad máxima. La energía almacenada fluctúa según un patrón sinusoidal que simula el consumo y la carga de energía.

## Información en las gráficas

El script presenta varias gráficas para visualizar el estado de la red:

- **Red de Nodos**: Muestra los suministradores, distribuidores y estaciones. Los colores y tamaños de los nodos cambian según el nivel de energía.
- **Gráfico de evolución temporal**: Visualiza estadísticas clave, como:
  - Estaciones al 0% o 100% de carga.
  - Carga media de estaciones.
  - Producción media de suministradores.
  - Porcentaje de carga total en la red.
- **Gráfico de barras (derecha)**: Muestra la carga total de distribuidores, estaciones, y la capacidad libre de las estaciones.
- **Mix energético (izquierda)**: Desglosa la producción total de energía por tipo (Solar, Eólica, etc.).

## Dependencias

Para ejecutar este proyecto, asegúrate de tener instaladas las siguientes dependencias:

- `networkx`: Para la creación y manipulación de grafos.
- `matplotlib`: Para la visualización de gráficos.
- `numpy`: Para el manejo de funciones matemáticas avanzadas.
- `tkinter`: Para la interfaz gráfica.

Puedes instalarlas ejecutando:

```bash
pip install networkx matplotlib numpy
