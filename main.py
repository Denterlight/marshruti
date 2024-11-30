import osmnx as ox
from math import inf, sqrt
import matplotlib.pyplot as plt


def calculate_euclidean_distance(lat1, lon1, lat2, lon2):
    """
    Вычисляет евклидово расстояние между двумя точками
    """
    return sqrt((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2)


def find_nearest_node(G, lat, lon):
    """
    Находит ближайший узел к заданной точке
    """
    min_distance = float('inf')
    nearest_node = None

    for node, data in G.nodes(data=True):
        node_lat = data['y']
        node_lon = data['x']
        distance = calculate_euclidean_distance(lat, lon, node_lat, node_lon)

        if distance < min_distance:
            min_distance = distance
            nearest_node = node

    return nearest_node


def get_manhattan_graph(start_coord, end_coord):
    """
    Получает граф Манхэттена и находит ближайшие узлы к начальной и конечной точкам
    """
    # Разбираем координаты
    start_lat, start_lon = map(float, start_coord.split(','))
    end_lat, end_lon = map(float, end_coord.split(','))

    # Загружаем граф Манхэттена
    G = ox.graph_from_place('Manhattan, New York City, New York', network_type='drive')

    # Находим ближайшие узлы 
    start_node = find_nearest_node(G, start_lat, start_lon)
    end_node = find_nearest_node(G, end_lat, end_lon)

    # Создаем структуры данных для хранения узлов и ребер
    nodes = {}
    edges = []

    # Заполняем словарь узлов
    for node, data in G.nodes(data=True):
        nodes[str(node)] = {'lat': data['y'], 'lon': data['x']}

    # Заполняем список ребер
    for u, v, data in G.edges(data=True):
        length = data.get('length', 0)
        edges.append({
            'source': str(u),
            'target': str(v),
            'weight': length
        })

    return {
        'G': G,
        'nodes': nodes,
        'edges': edges,
        'start_node': str(start_node),
        'end_node': str(end_node)
    }


def dijkstra(graph, start, end):
    """
    Реализация алгоритма Дейкстры для поиска кратчайшего пути
    """
    # Инициализация расстояний
    distances = {node: inf for node in graph['nodes']}
    distances[start] = 0

    # Инициализация предшественников для восстановления пути
    predecessors = {node: None for node in graph['nodes']}

    # Создаем множество непосещенных узлов
    unvisited = set(graph['nodes'].keys())

    while unvisited:
        # Находим узел с минимальным расстоянием
        min_distance = inf
        current_node = None
        for node in unvisited:
            if distances[node] < min_distance:
                min_distance = distances[node]
                current_node = node

        if current_node == end:
            break

        unvisited.remove(current_node)

        # Проверяем всех соседей текущего узла
        for edge in graph['edges']:
            if edge['source'] == current_node:
                neighbor = edge['target']
                weight = edge['weight']

                # Если найден более короткий путь
                if distances[current_node] + weight < distances[neighbor]:
                    distances[neighbor] = distances[current_node] + weight
                    predecessors[neighbor] = current_node

    # Восстанавливаем путь
    path = []
    current_node = end
    while current_node is not None:
        path.append(current_node)
        current_node = predecessors[current_node]
    path.reverse()

    return distances[end], path


def visualize_path(G, path):
    """
    Создает простую визуализацию пути
    """
    # Преобразуем строковые идентификаторы в целые числа
    path = [int(node) for node in path]

    # Рисуем граф и путь
    ox.plot_graph_route(G, path,
                        node_size=0,
                        bgcolor='white',
                        edge_color='gray',
                        route_color='red',
                        route_linewidth=4,
                        route_alpha=0.7,
                        figsize=(15, 10))


def main():
    print("Введите координаты начальной точки в формате 'широта,долгота' (например: 40.7829,-73.9654):")
    start_coord = input().strip()

    print("Введите координаты конечной точки в формате 'широта,долгота' (например: 40.7580,-73.9855):")
    end_coord = input().strip()

    graph_data = get_manhattan_graph(start_coord, end_coord)

    shortest_distance, path = dijkstra(graph_data, graph_data['start_node'], graph_data['end_node'])

    result = round(shortest_distance, 2)
    print(f"Кратчайшее расстояние между точками: {result} метров")

    print("Создаю визуализацию маршрута...")
    visualize_path(graph_data['G'], path)


main()
