import osmnx as ox
from math import sqrt
import tkinter as tk
from tkinter import ttk, messagebox


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

    # Заполняем список ребер(список словарей ребер)
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
    distances = {node: float('inf') for node in graph['nodes']}
    distances[start] = 0

    # Инициализация предшественников для восстановления пути
    predecessors = {node: None for node in graph['nodes']}

    # Создаем множество непосещенных узлов
    unvisited = set(graph['nodes'].keys())

    while unvisited:
        # Находим узел с минимальным расстоянием
        min_distance = float('inf')
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


# Создаем главное окно
root = tk.Tk()
root.title("Расчёт городских автоперевозок")
root.geometry("400x300")

# Создаем рамку
main_frame = ttk.Frame(root, padding="10")
main_frame.grid(row=0, column=0)

# Создаем переменные для хранения данных визуализации
graph_data = None
path = None


# Функция для расчета расстояния
def calculate_distance():
    global graph_data, path
    try:
        # Получаем координаты из полей ввода
        start_coord = f"{start_lat.get()},{start_lon.get()}"
        end_coord = f"{end_lat.get()},{end_lon.get()}"

        # Проверяем формат координат
        try:
            start_lat_val, start_lon_val = map(float, start_coord.split(','))
            end_lat_val, end_lon_val = map(float, end_coord.split(','))
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат координат. Используйте числа для широты и долготы.")
            return

        # Получаем данные графа
        graph_data = get_manhattan_graph(start_coord, end_coord)

        # Рассчитываем кратчайший путь
        shortest_distance, path = dijkstra(graph_data, graph_data['start_node'], graph_data['end_node'])

        # Выводим результат
        result = round(shortest_distance, 2)
        result_label.config(text=f"Кратчайшее расстояние: {result} метров")

        # Показываем кнопку визуализации
        viz_button.grid()

    except Exception as e:
        messagebox.showerror("Ошибка", str(e))


# Функция для визуализации
def show_visualization():
    try:
        if graph_data and path:
            visualize_path(graph_data['G'], path)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось создать визуализацию: {str(e)}")


# Создаем элементы интерфейса
ttk.Label(main_frame, text="Начальная точка:").grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
ttk.Label(main_frame, text="Широта:").grid(row=1, column=0, sticky=tk.W)
start_lat = ttk.Entry(main_frame, width=15)
start_lat.grid(row=1, column=1, padx=5)
ttk.Label(main_frame, text="Долгота:").grid(row=1, column=2, sticky=tk.W)
start_lon = ttk.Entry(main_frame, width=15)
start_lon.grid(row=1, column=3, padx=5)

ttk.Label(main_frame, text="Конечная точка:").grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
ttk.Label(main_frame, text="Широта:").grid(row=3, column=0, sticky=tk.W)
end_lat = ttk.Entry(main_frame, width=15)
end_lat.grid(row=3, column=1, padx=5)
ttk.Label(main_frame, text="Долгота:").grid(row=3, column=2, sticky=tk.W)
end_lon = ttk.Entry(main_frame, width=15)
end_lon.grid(row=3, column=3, padx=5)

ttk.Label(main_frame, text="Пример: 40.7829, -73.9654").grid(row=4, column=0, columnspan=4, pady=5)

calc_button = ttk.Button(main_frame, text="Рассчитать расстояние", command=calculate_distance)
calc_button.grid(row=5, column=0, columnspan=4, pady=10)

result_label = ttk.Label(main_frame, text="")
result_label.grid(row=6, column=0, columnspan=4, pady=5)

viz_button = ttk.Button(main_frame, text="Визуализация", command=show_visualization)
viz_button.grid(row=7, column=0, columnspan=4, pady=10)
viz_button.grid_remove()  # Скрываем кнопку


root.mainloop()
