import networkx as nx
from collections import deque
import copy

class game:
    static_graph = None  # 存一個固定圖，所有實例共用
    
    def __init__(self, index_dict={"R":(0,0),"B":(0,1),"G":(1,0),"Y":(1,1),"P":(2,0)}, boy_index="R2"):
        self.index_dict = index_dict
        self.boy_index = boy_index
        if game.static_graph is None:
            game.static_graph = game._generate_static_graph()    # 如果還沒建就建立一次

    @staticmethod
    def _generate_static_graph():
        # 生成固定不變的靜態圖
        G = nx.Graph()  
        Color_list = ['red', 'blue', 'green', "yellow","purple"]
        category_list = ['R', 'B', 'G', "Y", "P"]
        direction_list = [1, 2, 3, 4, 5, 6]

        for category in range(len(category_list)):
            for direction in direction_list:
                name = category_list[category] + str(direction)
                G.add_node(name, 
                           category=category_list[category], 
                           description=direction, 
                           color=Color_list[category],
                           label="")

        # 指定 label
        G.nodes["R5"]["label"] = 'Door'
        G.nodes["R1"]["label"] = 'Y'
        G.nodes["R3"]["label"] = 'P'

        G.nodes["G6"]["label"] = 'Key'
        G.nodes["G2"]["label"] = 'Y'
        G.nodes["G4"]["label"] = 'B'

        G.nodes["B1"]["label"] = 'G'
        G.nodes["B5"]["label"] = 'P'

        G.nodes["Y1"]["label"] = 'R'
        G.nodes["Y6"]["label"] = 'G'

        G.nodes["P3"]["label"] = 'R'
        G.nodes["P4"]["label"] = 'B'

        # 邊
        G.add_edges_from([("R1", "R2"), ("R2", "R6"), ("R1", "R6"), ("R3", "R4")])
        G.add_edges_from([("B1", "B2"), ("B3", "B4"), ("B6", "B3"), ("B4", "B6")])
        G.add_edges_from([("G1", "G5"), ("G2", "G3")])
        G.add_edges_from([("Y1", "Y2"), ("Y3", "Y2"), ("Y1", "Y3"), ("Y4", "Y5")])
        G.add_edges_from([("P1", "P6"), ("P2", "P4")])
        return G



    def generate_graph(self):
        # 1️⃣ 先蒐集所有要動態加的邊到一個 list
        dynamic = []
        index_dict = self.index_dict
        keylist   = list(index_dict.keys())
        valuelist = list(index_dict.values())
        for i in range(len(keylist)):
            for j in range(i+1, len(keylist)):
                x1, y1 = valuelist[i]
                x2, y2 = valuelist[j]
                # 注意：這裡要 append 到 dynamic，而不是直接呼叫 G.add_edge
                if x1 - x2 == -1 and y1 - y2 == 0:
                    dynamic.append((keylist[i] + "1", keylist[j] + "4"))
                elif x1 - x2 == 0 and y1 - y2 == -1:
                    dynamic.append((keylist[i] + "2", keylist[j] + "5"))
                elif x1 - x2 == 1 and y1 - y2 == -1:
                    dynamic.append((keylist[i] + "3", keylist[j] + "6"))
                elif x1 - x2 == 1 and y1 - y2 == 0:
                    dynamic.append((keylist[i] + "4", keylist[j] + "1"))
                elif x1 - x2 == 0 and y1 - y2 == 1:
                    dynamic.append((keylist[i] + "5", keylist[j] + "2"))
                elif x1 - x2 == -1 and y1 - y2 == 1:
                    dynamic.append((keylist[i] + "6", keylist[j] + "3"))

        # 2️⃣ 把動態邊生出獨立的小圖
        dynG = nx.Graph()
        dynG.add_edges_from(dynamic)

        # 3️⃣ 用 compose 合併 static 與 dynamic
        #    compose 只會建一次新圖，底層是 C 實作，效能很高
        return nx.compose(game.static_graph, dynG)


# 查詢 Node 所有連通的控制桿
    def node_connected_label(self):
        G = self.generate_graph()
        labellist={}
        connected_nodes = list(nx.node_connected_component(G, self.boy_index))
        for name in connected_nodes:
            node=G.nodes[name]
            if node["label"] in ['R', 'B', 'G', "Y", "P"]:
                labellist[name]=node["label"]
        return labellist

#輸入板塊位置與欲移動板塊獲得可移動位置
    def Legal_movement(self, plate):
        #在index_dict中plate可移動位置
        index_dict = self.index_dict
        new_index_set = set()  
        adj_list = [(0,1), (1,0), (-1,0), (0,-1), (-1,1), (1,-1)]
        occupied_positions = set(index_dict.values())  # 轉為 set 加速查找
        for key, (x1, y1) in index_dict.items():
            if key == plate:
                continue  # 跳過 plate 這個 key
            for dx, dy in adj_list:
                new_pos = (x1 + dx, y1 + dy)
                if new_pos not in occupied_positions and new_pos not in new_index_set:
                    new_index_set.add(new_pos)
        return list(new_index_set) 
    
#是否與key相連
    def find_key(self):
        G = self.generate_graph()
        connected_nodes = list(nx.node_connected_component(G, self.boy_index))
        for name in connected_nodes:
            node=G.nodes[name]
            if node["label"] == "Key":
                return True
        return False

#是否與door相連
    def find_door(self):
        G = self.generate_graph()
        connected_nodes = list(nx.node_connected_component(G, self.boy_index))
        for name in connected_nodes:
            node=G.nodes[name]
            if node["label"] == "Door":
                return True
        return False

    def Legal_Action(self):
        action_list = []

        # 1️⃣ 先產生目前的圖與連通集，只做一次
        G0 = self.generate_graph()
        boy0 = self.boy_index
        prev_conn = set(nx.node_connected_component(G0, boy0))

        # 2️⃣ 挑出所有可操作的控制桿節點及其顏色
        labellist = {
            node: G0.nodes[node]['label']
            for node in prev_conn
            if G0.nodes[node]['label'] in ['R','B','G','Y','P']
        }

        # 3️⃣ 選擇一般移動 or 特殊移動
        move_func = (
            self.find_special_movements
            if len(labellist) == 1
            else self.Legal_movement
        )

        # 4️⃣ 對每個操作，判斷是否創造新路
        for key, label in labellist.items():
            for index in move_func(label):
                # 建立 child 狀態
                new_idx = dict(self.index_dict)
                new_idx[label] = index
                child_game = game(new_idx, key)

                # 算 child 的連通集
                G1 = child_game.generate_graph()
                boy1 = child_game.boy_index
                child_conn = set(nx.node_connected_component(G1, boy1))

                # —— 這裡改用 boy_label 判斷是否「新路徑」 —— 
                boy_label = G1.nodes[boy1]["label"]
                creates_new = any(n[0] == boy_label for n in child_conn)

                action_list.append((key, label, index, creates_new))

        return action_list



#輸入index獲得相對位置
    def Relative_Position(self, move_index):
        x1,y1=move_index
        adj_list = [(-1,0), (0,-1), (1,-1), (1,0), (0,1), (-1,1)]
        for i , (dx, dy) in enumerate(adj_list):
            for color, index in self.index_dict.items():
                if (x1+dx,y1+dy) == index:
                    return color+str(i+1)
        print("輸入錯誤")
        return "錯誤"
    
    # 查詢與 boy 相連的所有節點，並篩選 degree=1 的節點
    def find_special_movements(self, plate):
        adj_list = [(-1,0), (0,-1), (1,-1), (1,0), (0,1), (-1,1)]
        G = self.generate_graph()
        connected_nodes = list(nx.node_connected_component(G, self.boy_index))  # 取得與玩家相連的所有節點
        # print(connected_nodes)
        result_nodes = set()
        for node in connected_nodes:
            if node[0]!= plate:
                x1,y1=self.index_dict[node[0]]
                dic=int(node[1])
                dx,dy=adj_list[dic-1]
                x2,y2=x1-dx,y1-dy
                if (x2,y2) not in self.index_dict.values():
                    result_nodes.add((x2,y2))
        return list(result_nodes)





class Node:
    def __init__(self, game, parent=None, move=None, key=False, success=False, creates_new_path=False):
        self.game = game            # 當前遊戲狀態（複製版本）
        # self.G = self.game.generate_graph()
        self.parent = parent      # 父節點
        self.move = move
        self.key = key            # 從父節點移動到此節點所採取的走法
        self.success = success
        self.children = []
        self.creates_new_path = creates_new_path
        self.state_base = frozenset(self.game.index_dict.items())


def backup(node):
    answer_list = []
    key_found = False

    while node is not None:
        if not node.key and not key_found:
            answer_list.insert(1, "K")
            key_found = True
        if node.parent is None:
            break
        move_index = node.game.Relative_Position(node.move)
        boy = node.game.boy_index
        label = node.game.generate_graph().nodes[boy]["label"]
        answer_list.insert(0, f"{boy[0]}{label}{move_index}")
        node = node.parent

    answer_list.append("D")
    if "K" not in answer_list:
        answer_list.insert(0, "K")
    return answer_list


def decode_moves(code_list):
    color_map = {
        'R': '紅色',
        'Y': '黃色',
        'G': '綠色',
        'B': '藍色',
        'P': '紫色'
    }

    direction_map = {
        '1': '右方',
        '2': '右上',
        '3': '左上',
        '4': '左方',
        '5': '左下',
        '6': '右下'
    }

    output_lines = []
    step = 1

    for code in code_list:
        if code == 'K':
            output_lines.append("找到鑰匙")
        elif code == 'D':
            output_lines.append("找到大門")
        else:
            src = color_map[code[0]]
            target = color_map[code[1]]
            dest = color_map[code[2]]
            direction = direction_map[code[3]]
            line = f"{step}.走到{src}將{target}移動到{dest}{direction}"
            output_lines.append(line)
            step += 1

    return "\n".join(output_lines)


def run(Index_dict, Boy_index, iterations=10):
    Game = game(Index_dict, Boy_index)
    root = Node(Game, parent=None, move=None, key=False, success=False)
    root.key = root.game.find_key()

    def make_state_key(node):
        return (frozenset(node.game.index_dict.items()), node.key, node.game.boy_index)

    state_map = {}
    depth_map = {}
    q = deque([(root, 0)])

    sk0 = make_state_key(root)
    state_map[sk0] = root
    depth_map[sk0] = 0

    while q:
        node, depth = q.popleft()

        if depth >= iterations:
            continue

        if node.key and node.game.find_door():
            answer_list = backup(node)
            answer=decode_moves(answer_list)
            return {
                "solution": answer,
                "optimal_steps": len(answer_list) - 2
            }

        for point, label, index, creates_new in node.game.Legal_Action():
            new_index = dict(node.game.index_dict)
            new_index[label] = index
            new_game = game(new_index, point)
            new_key = node.key or new_game.find_key()

            state_key = (frozenset(new_index.items()), new_key, new_game.boy_index)
            new_depth = depth + 1

            if state_key not in state_map:
                child = Node(new_game, parent=node, move=index, key=new_key, success=False, creates_new_path=creates_new)
                state_map[state_key] = child
                depth_map[state_key] = new_depth
                node.children.append(child)
                q.append((child, new_depth))

    # 若沒有找到任何可行解
    return {
        "solution": "無可行解",
        "optimal_steps": "請重新排列題目"
    }


#狀態紀錄 1.板塊位置 2.boy位置 3.鑰匙狀態

def startindex(color):
        color_list = ['R', 'B', 'G', "Y", "P"]
        boy_list = [2,3,1,2,1]
        num = boy_list[color_list.index(color)]
        return color+str(num)


def solve_puzzle(index_dict, boy_index, max_depth=10):
    """
    主解題函數，接收 index_dict 與 boy_index，回傳一組合法解與步數。
    
    Parameters:
        index_dict (dict): 5個板塊顏色與位置對應，如 {"R": (0,0), "G": (0,1), ...}
        boy_index (str): 起始位置，如 "G1"
        max_depth (int): 搜索最大深度（預設10）
        
    Returns:
        dict: {
            "solution": ['K', 'GYP3', ..., 'D'],
            "optimal_steps": 整數步數 或 None（若無解）
        }
    """
    result = run(index_dict, boy_index, iterations=max_depth)
    return result



# Index_dict = {"R": (0, -1), "G": (0, 0), "Y": (-1, 0), "B": (0, 1), "P": (1, 0)}
# Boy_index = startindex("G")
# max_depth = 9

# result = solve_puzzle(Index_dict, Boy_index, max_depth)
# print(result["solution"])         # 印出動作序列
# print(result["optimal_steps"])    # 印出最佳步數





