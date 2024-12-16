import osmnx as ox
from math import sqrt
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime


# Создаем или подключаемся к базе данных
conn = sqlite3.connect('app_data.db')
cursor = conn.cursor()

# Создаем таблицы пользователей, машин и логов
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    car INT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS cars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    brand TEXT NOT NULL,
    color TEXT NOT NULL,
    number TEXT NOT NULL,
    typeC TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    search_time TEXT NOT NULL,
    start_coords TEXT NOT NULL,
    end_coords TEXT NOT NULL,
    distance REAL NOT NULL
)
""")

conn.commit()


def calculate_euclidean_distance(lat1, lon1, lat2, lon2):
    """Вычисляет евклидово расстояние между двумя точками."""
    return sqrt((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2)


def find_nearest_node(G, lat, lon):
    """Находит ближайший узел к заданной точке."""
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


def get_city_graph(start_coord, end_coord):
    """
    Получает граф города и находит ближайшие узлы к начальной и конечной точкам
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
    """Создает простую визуализацию пути."""
    path = [int(node) for node in path]
    ox.plot_graph_route(G, path, node_size=0, bgcolor='white', edge_color='gray',
                        route_color='red', route_linewidth=4, route_alpha=0.7, figsize=(15, 10))


def login_screen():
    """Экран логина и регистрации."""
    def login():
        username = username_entry.get()
        password = password_entry.get()
        # Проверка на администратора
        if username == 'admin' and password == 'admin':
            admin_screen()
        else:
            cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
            user = cursor.fetchone()
            if user:
                main_screen(username)
            else:
                messagebox.showerror("Ошибка", "Неверный логин или пароль!")


    login_window = tk.Toplevel()
    login_window.title("Вход")
    login_window.geometry("300x200")

    ttk.Label(login_window, text="Логин:").grid(row=0, column=0, padx=10, pady=5)
    username_entry = ttk.Entry(login_window)
    username_entry.grid(row=0, column=1, padx=10, pady=5)

    ttk.Label(login_window, text="Пароль:").grid(row=1, column=0, padx=10, pady=5)
    password_entry = ttk.Entry(login_window, show='*')
    password_entry.grid(row=1, column=1, padx=10, pady=5)

    ttk.Button(login_window, text="Войти", command=login).grid(row=2, column=0, columnspan=2, pady=10)


def admin_screen():
    """Экран администратора."""
    def add_user():
        """Добавление нового пользователя."""
        def save_user():
            username = username_entry.get()
            password = password_entry.get()
            first_name = first_name_entry.get()
            last_name = last_name_entry.get()
            phone = phone_entry.get()

            if not all([username, password, first_name, last_name, phone]):
                messagebox.showerror("Ошибка", "Все поля должны быть заполнены!")
                return

            try:
                cursor.execute(
                    "INSERT INTO users (username, password, first_name, last_name, phone) VALUES (?, ?, ?, ?, ?)",
                    (username, password, first_name, last_name, phone)
                )
                conn.commit()
                messagebox.showinfo("Успех", "Пользователь успешно добавлен!")
                add_user_window.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Ошибка", "Пользователь с таким логином уже существует!")

        add_user_window = tk.Toplevel()
        add_user_window.title("Добавление пользователя")
        add_user_window.geometry("300x300")

        ttk.Label(add_user_window, text="Логин:").grid(row=0, column=0, padx=10, pady=5)
        username_entry = ttk.Entry(add_user_window)
        username_entry.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(add_user_window, text="Пароль:").grid(row=1, column=0, padx=10, pady=5)
        password_entry = ttk.Entry(add_user_window)
        password_entry.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(add_user_window, text="Имя:").grid(row=2, column=0, padx=10, pady=5)
        first_name_entry = ttk.Entry(add_user_window)
        first_name_entry.grid(row=2, column=1, padx=10, pady=5)

        ttk.Label(add_user_window, text="Фамилия:").grid(row=3, column=0, padx=10, pady=5)
        last_name_entry = ttk.Entry(add_user_window)
        last_name_entry.grid(row=3, column=1, padx=10, pady=5)

        ttk.Label(add_user_window, text="Телефон:").grid(row=4, column=0, padx=10, pady=5)
        phone_entry = ttk.Entry(add_user_window)
        phone_entry.grid(row=4, column=1, padx=10, pady=5)

        ttk.Button(add_user_window, text="Сохранить", command=save_user).grid(row=5, column=0, columnspan=2, pady=10)

    def add_car():
        """Добавление нового автомобиля."""
        def save_car():
            user_id = user_id_entry.get()
            brand = brand_entry.get()
            color = color_entry.get()
            number = number_entry.get()
            typeC = typeC_entry.get()

            if not all([user_id, brand, color, number, typeC]):
                messagebox.showerror("Ошибка", "Все поля должны быть заполнены!")
                return


            cursor.execute(
                "INSERT INTO cars (user_id, brand, color, number, typeC) VALUES (?, ?, ?, ?, ?)",
                (user_id, brand, color, number, typeC)
            )
            conn.commit()
            messagebox.showinfo("Успех", "Автомобиль успешно добавлен!")
            add_car_window.destroy()


        add_car_window = tk.Toplevel()
        add_car_window.title("Добавление автомобиля")
        add_car_window.geometry("300x300")

        ttk.Label(add_car_window, text="ID пользователя:").grid(row=0, column=0, padx=10, pady=5)
        user_id_entry = ttk.Entry(add_car_window)
        user_id_entry.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(add_car_window, text="<Бренд>:").grid(row=1, column=0, padx=10, pady=5)
        brand_entry = ttk.Entry(add_car_window)
        brand_entry.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(add_car_window, text="Цвет:").grid(row=2, column=0, padx=10, pady=5)
        color_entry = ttk.Entry(add_car_window)
        color_entry.grid(row=2, column=1, padx=10, pady=5)

        ttk.Label(add_car_window, text="Номер:").grid(row=3, column=0, padx=10, pady=5)
        number_entry = ttk.Entry(add_car_window)
        number_entry.grid(row=3, column=1, padx=10, pady=5)

        ttk.Label(add_car_window, text="Тип:").grid(row=4, column=0, padx=10, pady=5)
        typeC_entry = ttk.Entry(add_car_window)
        typeC_entry.grid(row=4, column=1, padx=10, pady=5)

        ttk.Button(add_car_window, text="Сохранить", command=save_car).grid(row=5, column=0, columnspan=2, pady=10)

    def view_logs():
        """Просмотр логов."""
        logs_window = tk.Toplevel()
        logs_window.title("Логи")
        logs_window.geometry("600x400")

        logs_tree = ttk.Treeview(logs_window, columns=("username", "time", "start", "end", "distance"), show="headings")
        logs_tree.heading("username", text="Пользователь")
        logs_tree.heading("time", text="Время поиска")
        logs_tree.heading("start", text="Начальные координаты")
        logs_tree.heading("end", text="Конечные координаты")
        logs_tree.heading("distance", text="Расстояние")
        logs_tree.pack(fill=tk.BOTH, expand=True)

        cursor.execute("SELECT username, search_time, start_coords, end_coords, distance FROM logs")
        for log in cursor.fetchall():
            logs_tree.insert("", tk.END, values=log)

    def view_usersd():
        users_window = tk.Toplevel()
        users_window.title("Пользователи")
        users_window.geometry("600x600")

        users_tree = ttk.Treeview(users_window, columns=("id", "username", "password", "first_name", "last_name", "phone"), show="headings")
        users_tree.heading("id", text="ID")
        users_tree.heading("username", text="Логин")
        users_tree.heading("password", text="Пароль")
        users_tree.heading("first_name", text="Имя")
        users_tree.heading("last_name", text="Фамилия")
        users_tree.heading("phone", text="Телефон")
        users_tree.pack(fill=tk.BOTH, expand=True)

        cursor.execute("SELECT * FROM users")
        for user in cursor.fetchall():
            users_tree.insert("", tk.END, values=user)

    def view_cars():
        cars_window = tk.Toplevel()
        cars_window.title("Автомобили")
        cars_window.geometry("1000x600")

        cars_tree = ttk.Treeview(cars_window, columns=("id", "user_id", "brand", "color", "number", "typeC"))
        cars_tree.heading("id", text="ID")
        cars_tree.heading("user_id", text="ID пользователя")
        cars_tree.heading("brand", text="Марка")
        cars_tree.heading("color", text="Цвет")
        cars_tree.heading("number", text="Номер")
        cars_tree.heading("typeC", text="Тип")
        cars_tree.pack(fill=tk.BOTH, expand=True)

        cursor.execute("SELECT * FROM cars")
        for car in cursor.fetchall():
            cars_tree.insert("", tk.END, values=car)


    admin_window = tk.Toplevel()
    admin_window.title("Админ")
    admin_window.geometry("350x350")

    ttk.Button(admin_window, text="Добавить пользователя", command=add_user).grid(row=0, column=0, pady=10, padx=10)
    ttk.Button(admin_window, text="Просмотреть логи", command=view_logs).grid(row=1, column=0, pady=10, padx=10)
    ttk.Button(admin_window, text="Просмотреть пользователей", command=view_usersd).grid(row=2, column=0, pady=10, padx=10)
    ttk.Button(admin_window, text="Просмотреть автомобили", command=view_cars).grid(row=3, column=0, pady=10, padx=10)
    ttk.Button(admin_window, text="Добавить автомобиль", command=add_car).grid(row=4, column=0, pady=10, padx=10)

def main_screen(username):
    """Главный экран для пользователя."""
    def calculate_distance():
        global graph_data, path
        try:
            start_coord = f"{start_lat.get()},{start_lon.get()}"
            end_coord = f"{end_lat.get()},{end_lon.get()}"

            start_lat_val, start_lon_val = map(float, start_coord.split(','))
            end_lat_val, end_lon_val = map(float, end_coord.split(','))

            graph_data = get_city_graph(start_coord, end_coord)
            shortest_distance, path = dijkstra(graph_data, graph_data['start_node'], graph_data['end_node'])

            result = round(shortest_distance, 2)
            result_label.config(text=f"Кратчайшее расстояние: {result} метров")

            cursor.execute(
                "INSERT INTO logs (username, search_time, start_coords, end_coords, distance) VALUES (?, ?, ?, ?, ?)",
                (username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), start_coord, end_coord, result)
            )
            conn.commit()

            viz_button.grid()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def show_visualization():
        try:
            if graph_data and path:
                visualize_path(graph_data['G'], path)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать визуализацию: {str(e)}")

    user_window = tk.Toplevel()
    user_window.title(f"Пользователь: {username}")
    user_window.geometry("400x300")

    main_frame = ttk.Frame(user_window, padding="10")
    main_frame.grid(row=0, column=0)

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
    viz_button.grid_remove()


# Запуск приложения
root = tk.Tk()
root.title("Городские автоперевозки")
root.geometry("300x200")
ttk.Button(root, text="Войти", command=login_screen).pack(pady=50)
root.mainloop()

# Закрываем соединение с базой данных при завершении работы
conn.close()
