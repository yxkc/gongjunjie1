# 优先设置Matplotlib后端（必须在导入pyplot前执行）
import matplotlib
matplotlib.use('Agg')

import streamlit as st
import sqlite3
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import io

# ===================== 全局配置 =====================
st.set_page_config(
    page_title="商店管理系统",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 获取应用基础目录（兼容所有系统）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 商品图片存储目录（相对路径）
PHOTO_DIR = os.path.join(BASE_DIR, "product_photos")
# 数据库文件路径（相对路径）
DB_FILE = os.path.join(BASE_DIR, "store_management.db")

# Matplotlib 中文支持配置
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示异常

# 颜色常量定义
PRIMARY_COLOR = "#2c3e50"
SECONDARY_COLOR = "#3498db"
ACCENT_COLOR = "#e74c3c"
SUCCESS_COLOR = "#27ae60"
WARNING_COLOR = "#f39c12"
BACKGROUND_COLOR = "#f8f9fa"
CARD_BG_COLOR = "#ffffff"
TABLE_HEADER_COLOR = "#e9ecef"

# 全局样式美化
st.markdown(f"""
    <style>
    .stApp {{
        background-color: {BACKGROUND_COLOR};
        padding: 1rem 2rem;
    }}
    .main-title {{
        color: {PRIMARY_COLOR};
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 2rem;
        text-align: center;
        letter-spacing: 1px;
    }}
    .stCard, [data-testid="stVerticalBlock"] > [data-testid="stContainer"] {{
        background-color: {CARD_BG_COLOR};
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 1.5rem;
        border: 1px solid rgba(0,0,0,0.02);
    }}
    h2 {{
        color: {PRIMARY_COLOR};
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 1rem;
        border-left: 4px solid {SECONDARY_COLOR};
        padding-left: 0.8rem;
    }}
    .stButton>button {{
        background-color: {SECONDARY_COLOR};
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        height: 45px !important;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 !important;
        padding: 0 16px !important;
        transition: all 0.2s ease;
    }}
    .stButton>button:hover {{
        background-color: {PRIMARY_COLOR};
        box-shadow: 0 2px 8px rgba(52, 152, 219, 0.3);
    }}
    .danger-btn>button {{
        background-color: {ACCENT_COLOR} !important;
        height: 45px !important;
        width: 100% !important;
        margin: 0 !important;
    }}
    .danger-btn>button:hover {{
        background-color: #c0392b !important;
        box-shadow: 0 2px 8px rgba(231, 76, 60, 0.3) !important;
    }}
    .success-btn>button {{
        background-color: {SUCCESS_COLOR} !important;
        height: 45px !important;
        width: 100% !important;
        margin: 0 !important;
    }}
    .success-btn>button:hover {{
        background-color: #219653 !important;
        box-shadow: 0 2px 8px rgba(39, 174, 96, 0.3) !important;
    }}
    .warning-btn>button {{
        background-color: {WARNING_COLOR} !important;
        height: 45px !important;
        width: 100% !important;
        margin: 0 !important;
    }}
    .warning-btn>button:hover {{
        background-color: #e67e22 !important;
        box-shadow: 0 2px 8px rgba(243, 156, 18, 0.3) !important;
    }}
    .dataframe {{
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
        border: 1px solid rgba(0,0,0,0.05);
    }}
    .dataframe thead th {{
        background-color: {TABLE_HEADER_COLOR} !important;
        font-weight: 600;
        color: {PRIMARY_COLOR};
    }}
    .product-photo-card {{
        background-color: {CARD_BG_COLOR};
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 1rem;
        transition: all 0.2s ease;
    }}
    .product-photo-card:hover {{
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        transform: translateY(-2px);
    }}
    .btn-group {{
        margin-top: 1.5rem;
        width: 100%;
    }}
    [data-testid="stButton"] button {{
        height: 45px !important;
        width: 100% !important;
        margin: 0 !important;
    }}
    [data-testid="stTextInput"], [data-testid="stNumberInput"], [data-testid="stSelectbox"] {{
        margin-bottom: 1rem;
    }}
    [data-testid="stTextInput"] > div > div, 
    [data-testid="stNumberInput"] > div > div, 
    [data-testid="stSelectbox"] > div > div {{
        border-radius: 6px;
        border: 1px solid rgba(0,0,0,0.1);
    }}
    </style>
""", unsafe_allow_html=True)

# ===================== 数据库管理类 =====================
class DatabaseManager:
    def __init__(self, db_name=DB_FILE):
        self.db_name = db_name
        self.photo_dir = PHOTO_DIR
        # 创建图片目录（若不存在）
        if not os.path.exists(self.photo_dir):
            os.makedirs(self.photo_dir)
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 1. 员工表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff (
                staff_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                position TEXT NOT NULL
            )
        ''')
        
        # 仅当表为空时初始化默认员工数据
        cursor.execute("SELECT COUNT(*) FROM staff")
        if cursor.fetchone()[0] == 0:
            staff_members = [
                ("staff001", "张三", "管理员"),
                ("staff002", "李四", "收银员"),
                ("staff003", "王五", "仓库管理员"),
                ("staff004", "赵六", "采购员")
            ]
            cursor.executemany('''
                INSERT INTO staff (staff_id, name, position) 
                VALUES (?, ?, ?)
            ''', staff_members)
        
        # 2. 用户表（关联员工表）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                staff_id TEXT,
                role TEXT DEFAULT 'user',
                FOREIGN KEY (staff_id) REFERENCES staff(staff_id)
            )
        ''')
        
        # 仅当表为空时初始化默认用户数据
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO users (username, password, staff_id, role) 
                VALUES (?, ?, ?, ?)
            ''', ("user", "123456", "staff001", "admin"))
            cursor.execute('''
                INSERT INTO users (username, password, staff_id, role) 
                VALUES (?, ?, ?, ?)
            ''', ("test", "123456", "staff002", "user"))
        
        # 3. 商品表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                product_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                category TEXT NOT NULL,
                staff_id TEXT NOT NULL,
                photo_path TEXT,
                FOREIGN KEY (staff_id) REFERENCES staff(staff_id)
            )
        ''')
        
        # 批量初始化商品（仅表为空时执行，不预设图片路径）
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            product_list = [
                ("p001", "土豆", 2.5, 100, "蔬菜", "staff001", ""),
                ("p002", "鸡肉", 15.8, 50, "肉类", "staff001", ""),
                ("p003", "牛肉", 38.6, 30, "肉类", "staff001", ""),
                ("p004", "辣椒", 3.2, 80, "蔬菜", "staff001", ""),
                ("p005", "面包", 4.5, 60, "食品", "staff001", ""),
                ("p006", "胡萝卜", 2.8, 70, "蔬菜", "staff001", ""),
                ("p007", "快餐面", 5.0, 120, "食品", "staff001", ""),
                ("p008", "牙膏", 9.9, 90, "日用品", "staff001", ""),
                ("p009", "洗发水", 25.8, 40, "日用品", "staff001", ""),
                ("p010", "笔记本", 8.5, 75, "文具", "staff001", ""),
            ]
            cursor.executemany('''
                INSERT INTO products (product_id, name, price, quantity, category, staff_id, photo_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', product_list)
        
        # 4. 销售记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                sale_date TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        ''')
        
        # 5. 库存操作记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_operations (
                operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                operation_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                operation_date TEXT NOT NULL,
                staff_id TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (product_id) REFERENCES products(product_id),
                FOREIGN KEY (staff_id) REFERENCES staff(staff_id)
            )
        ''')
        
        # 兼容旧表结构
        self._update_table_structure(cursor, "users")
        
        conn.commit()
        conn.close()
    
    def _update_table_structure(self, cursor, table_name):
        if table_name == "users":
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            if "staff_id" not in columns:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN staff_id TEXT")
            if "role" not in columns:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN role TEXT DEFAULT 'user'")

# ===================== 数据访问对象 =====================
class UserDAO:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def get_user(self, username):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.username, u.password, u.role, u.staff_id, s.name, s.position 
            FROM users u 
            LEFT JOIN staff s ON u.staff_id = s.staff_id 
            WHERE u.username = ?
        ''', (username,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    def add_user_with_staff(self, username, password, staff_id, role="user"):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT staff_id FROM staff WHERE staff_id = ?", (staff_id,))
            if not cursor.fetchone():
                return False, "员工ID不存在"
            cursor.execute('''
                INSERT INTO users (username, password, staff_id, role) 
                VALUES (?, ?, ?, ?)
            ''', (username, password, staff_id, role))
            conn.commit()
            return True, "注册成功"
        except sqlite3.IntegrityError:
            return False, "用户名已存在"
        finally:
            conn.close()

class ProductDAO:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def get_all_products(self):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.product_id, p.name, p.price, p.quantity, p.category, 
                   p.staff_id, s.name as staff_name, p.photo_path
            FROM products p
            LEFT JOIN staff s ON p.staff_id = s.staff_id
        ''')
        products = cursor.fetchall()
        conn.close()
        return products
    
    def get_product(self, product_id):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.product_id, p.name, p.price, p.quantity, p.category, 
                   p.staff_id, s.name as staff_name, p.photo_path
            FROM products p
            LEFT JOIN staff s ON p.staff_id = s.staff_id
            WHERE p.product_id = ?
        ''', (product_id,))
        product = cursor.fetchone()
        conn.close()
        return product
    
    def add_product(self, product_id, name, price, quantity, category, staff_id, photo_path=""):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO products (product_id, name, price, quantity, category, staff_id, photo_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (product_id, name, price, quantity, category, staff_id, photo_path))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def update_product(self, product_id, name, price, quantity, category, staff_id, photo_path=""):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE products 
            SET name = ?, price = ?, quantity = ?, category = ?, staff_id = ?, photo_path = ?
            WHERE product_id = ?
        ''', (name, price, quantity, category, staff_id, photo_path, product_id))
        conn.commit()
        row_count = cursor.rowcount
        conn.close()
        return row_count > 0
    
    def delete_product(self, product_id):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
        conn.commit()
        row_count = cursor.rowcount
        conn.close()
        return row_count > 0
    
    def update_product_quantity(self, product_id, quantity_change):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET quantity = quantity + ? WHERE product_id = ?", 
                      (quantity_change, product_id))
        conn.commit()
        row_count = cursor.rowcount
        conn.close()
        return row_count > 0
    
    def get_products_below_warning_threshold(self, threshold):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT product_id, name, quantity 
            FROM products 
            WHERE quantity <= ? 
        ''', (threshold,))
        products = cursor.fetchall()
        conn.close()
        return products

class SalesDAO:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def get_all_sales(self):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sales ORDER BY sale_date DESC")
        sales = cursor.fetchall()
        conn.close()
        return sales
    
    def add_sale(self, product_id, product_name, quantity, unit_price, total_price):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        sale_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO sales (product_id, product_name, quantity, unit_price, total_price, sale_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (product_id, product_name, quantity, unit_price, total_price, sale_date))
        conn.commit()
        conn.close()
        return True

class InventoryDAO:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def add_operation(self, product_id, operation_type, quantity, staff_id, notes=""):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        operation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO inventory_operations (product_id, operation_type, quantity, operation_date, staff_id, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (product_id, operation_type, quantity, operation_date, staff_id, notes))
        conn.commit()
        conn.close()
        return True
    
    def get_all_operations(self):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                io.operation_id, 
                io.product_id, 
                p.name, 
                io.operation_type, 
                io.quantity,
                io.operation_date, 
                s.name as staff_name, 
                io.notes,
                (SELECT SUM(
                    CASE 
                        WHEN io2.operation_type = 'in' THEN io2.quantity 
                        ELSE -io2.quantity 
                    END
                ) 
                FROM inventory_operations io2 
                WHERE io2.product_id = io.product_id 
                AND io2.operation_date <= io.operation_date) as stock_after_operation
            FROM inventory_operations io
            LEFT JOIN products p ON io.product_id = p.product_id
            LEFT JOIN staff s ON io.staff_id = s.staff_id
            ORDER BY io.operation_date DESC
        ''')
        operations = cursor.fetchall()
        conn.close()
        return operations

class StaffDAO:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def get_all_staff(self):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM staff")
        staff = cursor.fetchall()
        conn.close()
        return staff

# ===================== 全局初始化 =====================
db_manager = DatabaseManager()
user_dao = UserDAO(db_manager)
product_dao = ProductDAO(db_manager)
sales_dao = SalesDAO(db_manager)
inventory_dao = InventoryDAO(db_manager)
staff_dao = StaffDAO(db_manager)

# 初始化图片目录（兼容部署环境）
if not os.path.exists(PHOTO_DIR):
    os.makedirs(PHOTO_DIR)

# ===================== 自动登录逻辑（核心改造：使用st.query_params替代废弃API） =====================
def auto_login_from_url():
    """从URL参数中读取用户信息，自动完成登录验证（使用新版st.query_params）"""
    # 获取URL查询参数（新版API：直接通过st.query_params访问，无需调用方法）
    if "username" in st.query_params and st.query_params["username"]:
        username = st.query_params["username"]  # 新版API直接取值（无需[0]，自动处理单值参数）
        # 验证用户是否存在
        user = user_dao.get_user(username)
        if user:
            # 恢复登录状态
            st.session_state.logged_in = True
            st.session_state.user_info = {
                "username": user[0],
                "role": user[2],
                "staff_id": user[3],
                "staff_name": user[4],
                "position": user[5]
            }
            return True
    return False

# 初始化Streamlit会话状态
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "show_register" not in st.session_state:
    st.session_state.show_register = False

# 页面加载时，尝试自动登录
if not st.session_state.logged_in:
    auto_login_from_url()

# ===================== 登录/注册页面 =====================
def login_page():
    st.markdown('<div class="main-title">商店管理系统</div>', unsafe_allow_html=True)
    
    with st.container(border=True):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.subheader("用户登录")
            username = st.text_input("用户名", placeholder="请输入您的用户名")
            password = st.text_input("密码", placeholder="请输入您的密码", type="password")
            
            col_btn1, col_btn2 = st.columns(2, gap="small")
            with col_btn1:
                if st.button("登录", use_container_width=True, key="login_btn"):
                    if not username or not password:
                        st.error("用户名和密码不能为空！")
                    else:
                        user = user_dao.get_user(username)
                        if user:
                            if user[1] == password:
                                st.session_state.logged_in = True
                                st.session_state.user_info = {
                                    "username": user[0],
                                    "role": user[2],
                                    "staff_id": user[3],
                                    "staff_name": user[4],
                                    "position": user[5]
                                }
                                # 登录成功后，设置URL参数（新版API：直接赋值st.query_params）
                                st.query_params["username"] = username
                                st.success(f"欢迎 {user[4]}（{user[5]}）！")
                                st.rerun()
                            else:
                                st.error("密码错误！")
                        else:
                            st.error("用户名不存在！")
            
            with col_btn2:
                if st.button("注册", use_container_width=True, key="show_register_btn"):
                    st.session_state.show_register = True
                    st.rerun()
    
    if st.session_state.show_register:
        st.markdown("---")
        with st.container(border=True):
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.subheader("新用户注册")
                reg_username = st.text_input("新用户名", placeholder="请设置用户名", key="reg_username")
                reg_password = st.text_input("新密码", placeholder="请设置6位以上密码", type="password", key="reg_pwd")
                reg_pwd_confirm = st.text_input("确认密码", placeholder="请再次输入密码", type="password", key="reg_pwd_confirm")
                reg_staff_id = st.text_input("员工ID", placeholder="请输入关联员工ID（如staff001）", key="reg_staff_id")
                
                col_reg1, col_reg2 = st.columns(2, gap="small")
                with col_reg1:
                    if st.button("提交注册", use_container_width=True, key="submit_register_btn"):
                        if not reg_username or not reg_password or not reg_staff_id:
                            st.error("所有字段不能为空！")
                        elif len(reg_password) < 6:
                            st.error("密码长度不能少于6位！")
                        elif reg_password != reg_pwd_confirm:
                            st.error("两次密码不一致！")
                        else:
                            success, msg = user_dao.add_user_with_staff(reg_username, reg_password, reg_staff_id)
                            if success:
                                st.success(msg)
                                st.session_state.show_register = False
                                st.rerun()
                            else:
                                st.error(msg)
                with col_reg2:
                    if st.button("取消注册", use_container_width=True, key="cancel_register_btn"):
                        st.session_state.show_register = False
                        st.rerun()

# ===================== 主系统页面 =====================
def main_system():
    st.markdown(f"""
        <div style="background-color: {PRIMARY_COLOR}; padding: 1rem 2rem; border-radius: 12px; margin-bottom: 2rem; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h1 style="color: white; margin: 0; font-size: 24px; font-weight: 600;">商店管理系统</h1>
                <div style="color: white; font-size: 14px; background-color: rgba(255,255,255,0.1); padding: 0.5rem 1rem; border-radius: 6px;">
                    当前用户：{st.session_state.user_info['staff_name']}（{st.session_state.user_info['position']}）
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📦 商品管理", "💵 销售管理", "📊 库存管理", "📈 报表统计"])
    
    # 商品管理标签页
    with tab1:
        st.markdown('<div class="main-title">商品管理</div>', unsafe_allow_html=True)
        col_form, col_list = st.columns([1, 2], gap="large")
        
        with col_form:
            with st.container(border=True):
                st.subheader("商品信息维护")
                product_id = st.text_input("商品ID", placeholder="输入商品唯一ID", key="product_id")
                product_name = st.text_input("商品名称", placeholder="输入商品名称", key="product_name")
                product_price = st.number_input("商品价格", min_value=0.01, step=0.01, format="%.2f", key="product_price")
                product_quantity = st.number_input("商品数量", min_value=1, step=1, value=1, key="product_quantity")
                product_category = st.text_input("商品类别", placeholder="输入商品类别（如蔬菜/食品）", key="product_category")
                
                staff_list = staff_dao.get_all_staff()
                staff_options = [f"{s[0]} - {s[1]}" for s in staff_list]
                selected_staff = st.selectbox("录入人员", staff_options, key="product_staff_select") if staff_options else None
                staff_id = selected_staff.split(" - ")[0] if selected_staff else ""
                
                st.subheader("商品图片配置")
                uploaded_photo = st.file_uploader("上传新商品照片", type=["jpg", "jpeg", "png", "bmp"], key="product_photo_upload")
                # 动态获取现有图片（不硬编码）
                existing_photos = []
                if os.path.exists(PHOTO_DIR):
                    existing_photos = [f for f in os.listdir(PHOTO_DIR) if f.endswith((".jpg", ".jpeg", ".png", ".bmp"))]
                selected_photo = st.selectbox("选择已有图片（优先使用）", [""] + existing_photos, key="select_existing_photo")

                photo_path = ""
                if selected_photo and product_id:
                    photo_path = os.path.join(PHOTO_DIR, selected_photo)
                    st.success(f"已选择图片：{selected_photo}")
                elif uploaded_photo and product_id:
                    photo_filename = f"{product_id}_{uploaded_photo.name}"
                    photo_path = os.path.join(PHOTO_DIR, photo_filename)
                    with open(photo_path, "wb") as f:
                        f.write(uploaded_photo.getbuffer())
                    st.success(f"图片上传成功：{photo_filename}")
                
                st.markdown('<div class="btn-group">', unsafe_allow_html=True)
                col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4, gap="small")

                with col_btn1:
                    if st.button("添加商品", use_container_width=True, key="add_product_btn"):
                        if all([product_id, product_name, product_category, staff_id]):
                            if product_dao.add_product(product_id, product_name, product_price, product_quantity, product_category, staff_id, photo_path):
                                st.success("商品添加成功！")
                                st.rerun()
                            else:
                                st.error("商品ID已存在！")
                        else:
                            st.error("请填写完整信息！")

                with col_btn2:
                    if st.button("更新商品", use_container_width=True, key="update_product_btn"):
                        if all([product_id, product_name, product_category, staff_id]):
                            if product_dao.update_product(product_id, product_name, product_price, product_quantity, product_category, staff_id, photo_path):
                                st.success("商品更新成功！")
                                st.rerun()
                            else:
                                st.error("商品不存在！")
                        else:
                            st.error("请填写完整信息！")

                with col_btn3:
                    if st.button("删除商品", use_container_width=True, key="delete_product_btn"):
                        if product_id:
                            if st.confirm("确定要删除该商品吗？此操作不可恢复！"):
                                # 删除商品时同步删除图片
                                product_info = product_dao.get_product(product_id)
                                if product_info and product_info[7] and os.path.exists(product_info[7]):
                                    try:
                                        os.remove(product_info[7])
                                    except:
                                        pass
                                # 删除商品
                                if product_dao.delete_product(product_id):
                                    st.success("商品删除成功！")
                                    st.rerun()
                                else:
                                    st.error("商品不存在！")
                        else:
                            st.error("请输入商品ID！")
                    st.markdown(f"""
                        <style>
                        [data-testid="stButton"][data-key="delete_product_btn"] button {{
                            background-color: {ACCENT_COLOR} !important;
                        }}
                        [data-testid="stButton"][data-key="delete_product_btn"] button:hover {{
                            background-color: #c0392b !important;
                            box-shadow: 0 2px 8px rgba(231, 76, 60, 0.3) !important;
                        }}
                        </style>
                    """, unsafe_allow_html=True)

                with col_btn4:
                    if st.button("清空表单", use_container_width=True, key="clear_product_form_btn"):
                        st.rerun()
                    st.markdown(f"""
                        <style>
                        [data-testid="stButton"][data-key="clear_product_form_btn"] button {{
                            background-color: {WARNING_COLOR} !important;
                        }}
                        [data-testid="stButton"][data-key="clear_product_form_btn"] button:hover {{
                            background-color: #e67e22 !important;
                            box-shadow: 0 2px 8px rgba(243, 156, 18, 0.3) !important;
                        }}
                        </style>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        
        with col_list:
            with st.container(border=True):
                st.subheader("商品列表")
                products = product_dao.get_all_products()
                if products:
                    product_data = []
                    for p in products:
                        product_data.append({
                            "商品ID": p[0],
                            "商品名称": p[1],
                            "价格(¥)": f"{p[2]:.2f}",
                            "库存数量": p[3],
                            "商品类别": p[4],
                            "录入人员": p[6]
                        })
                    product_df = pd.DataFrame(product_data)
                    
                    def highlight_low_stock(val):
                        if val <= 5:
                            return f'background-color: #f8d7da; color: #721c24; font-weight: 500;'
                        elif val <= 30:
                            return f'background-color: #fff3cd; color: #856404; font-weight: 500;'
                        else:
                            return f'background-color: #d4edda; color: #155724; font-weight: 500;'
                    
                    st.dataframe(
                        product_df.style.applymap(highlight_low_stock, subset=["库存数量"]),
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    st.subheader("所有商品图片展示")
                    products_with_photo = [p for p in products if p[7] and os.path.exists(p[7])]
                    if products_with_photo:
                        with st.container(height=350, border=True):
                            cols_per_row = 3
                            rows = (len(products_with_photo) + cols_per_row - 1) // cols_per_row
                            
                            for row in range(rows):
                                start_idx = row * cols_per_row
                                end_idx = min(start_idx + cols_per_row, len(products_with_photo))
                                row_products = products_with_photo[start_idx:end_idx]
                                
                                cols = st.columns(len(row_products))
                                for col, product in zip(cols, row_products):
                                    with col:
                                        st.markdown('<div class="product-photo-card">', unsafe_allow_html=True)
                                        st.image(
                                            product[7], 
                                            caption=product[1], 
                                            width=120
                                        )
                                        st.write(f"商品ID：{product[0]}")
                                        st.write(f"价格：¥{product[2]:.2f}")
                                        st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.info("暂无商品上传图片，请先为商品添加照片！")
                else:
                    st.info("暂无商品数据，请添加商品！")
    
    # 销售管理标签页
    with tab2:
        st.markdown('<div class="main-title">销售管理</div>', unsafe_allow_html=True)
        col_form, col_list = st.columns([1, 2], gap="large")
        
        with col_form:
            with st.container(border=True):
                st.subheader("销售录入")
                sale_product_id = st.text_input("商品ID", placeholder="输入商品ID", key="sale_product_id")
                
                product_info = None
                if sale_product_id:
                    product_info = product_dao.get_product(sale_product_id)
                    if product_info:
                        st.success(f"找到商品：{product_info[1]}")
                        st.write(f"单价：¥{product_info[2]:.2f}")
                        st.write(f"当前库存：{product_info[3]}")
                    else:
                        st.error("未找到该商品！")
                
                sale_quantity = st.number_input("销售数量", min_value=1, step=1, value=1, key="sale_quantity")
                total_price = 0.0
                if product_info:
                    total_price = product_info[2] * sale_quantity
                    st.write(f"总价：¥{total_price:.2f}")
                
                st.markdown('<div class="btn-group">', unsafe_allow_html=True)
                col_btn1, col_btn2 = st.columns(2, gap="small")
                with col_btn1:
                    if st.button("完成销售", use_container_width=True, key="complete_sale_btn"):
                        if not sale_product_id or not product_info:
                            st.error("请先选择有效商品！")
                        elif sale_quantity > product_info[3]:
                            st.error(f"库存不足！当前库存：{product_info[3]}")
                        else:
                            sales_dao.add_sale(sale_product_id, product_info[1], sale_quantity, product_info[2], total_price)
                            product_dao.update_product_quantity(sale_product_id, -sale_quantity)
                            st.success(f"销售成功！总价：¥{total_price:.2f}")
                            st.rerun()
                    st.markdown(f"""
                        <style>
                        [data-testid="stButton"][data-key="complete_sale_btn"] button {{
                            background-color: {SUCCESS_COLOR} !important;
                        }}
                        [data-testid="stButton"][data-key="complete_sale_btn"] button:hover {{
                            background-color: #219653 !important;
                            box-shadow: 0 2px 8px rgba(39, 174, 96, 0.3) !important;
                        }}
                        </style>
                    """, unsafe_allow_html=True)
                
                with col_btn2:
                    if st.button("清空表单", use_container_width=True, key="clear_sale_form_btn"):
                        st.rerun()
                    st.markdown(f"""
                        <style>
                        [data-testid="stButton"][data-key="clear_sale_form_btn"] button {{
                            background-color: {WARNING_COLOR} !important;
                        }}
                        [data-testid="stButton"][data-key="clear_sale_form_btn"] button:hover {{
                            background-color: #e67e22 !important;
                            box-shadow: 0 2px 8px rgba(243, 156, 18, 0.3) !important;
                        }}
                        </style>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        
        with col_list:
            with st.container(border=True):
                st.subheader("销售记录")
                sales = sales_dao.get_all_sales()
                if sales:
                    sale_data = []
                    for s in sales:
                        sale_data.append({
                            "销售ID": s[0],
                            "商品ID": s[1],
                            "商品名称": s[2],
                            "销售数量": s[3],
                            "单价(¥)": f"{s[4]:.2f}",
                            "总价(¥)": f"{s[5]:.2f}",
                            "销售时间": s[6]
                        })
                    sale_df = pd.DataFrame(sale_data)
                    st.dataframe(sale_df, use_container_width=True, hide_index=True)
                else:
                    st.info("暂无销售记录，请完成首次销售！")
    
    # 库存管理标签页
    with tab3:
        st.markdown('<div class="main-title">库存管理</div>', unsafe_allow_html=True)
        col_form, col_list = st.columns([1, 2], gap="large")
        
        with col_form:
            with st.container(border=True):
                st.subheader("库存操作")
                inv_product_id = st.text_input("商品ID", placeholder="输入商品ID", key="inv_product_id")
                
                inv_product_info = None
                if inv_product_id:
                    inv_product_info = product_dao.get_product(inv_product_id)
                    if inv_product_info:
                        st.success(f"找到商品：{inv_product_info[1]}")
                        st.write(f"当前库存：{inv_product_info[3]}")
                    else:
                        st.error("未找到该商品！")
                
                operation_type = st.radio("操作类型", ["入库", "出库"], horizontal=True, key="inventory_op_type")
                inv_quantity = st.number_input("操作数量", min_value=1, step=1, value=1, key="inv_quantity")
                
                staff_list = staff_dao.get_all_staff()
                staff_options = [f"{s[0]} - {s[1]}" for s in staff_list]
                selected_inv_staff = st.selectbox("操作人员", staff_options, key="inv_staff_select") if staff_options else None
                inv_staff_id = selected_inv_staff.split(" - ")[0] if selected_inv_staff else ""
                
                inv_notes = st.text_input("备注", placeholder="输入操作备注（可选）", key="inv_notes")
                
                st.markdown('<div class="btn-group">', unsafe_allow_html=True)
                col_btn1, col_btn2 = st.columns(2, gap="small")
                with col_btn1:
                    if st.button("执行操作", use_container_width=True, key="execute_inv_op_btn"):
                        if not inv_product_id or not inv_product_info or not inv_staff_id:
                            st.error("请填写完整信息！")
                        elif operation_type == "出库" and inv_quantity > inv_product_info[3]:
                            st.error(f"库存不足！当前库存：{inv_product_info[3]}")
                        else:
                            quantity_change = inv_quantity if operation_type == "入库" else -inv_quantity
                            product_dao.update_product_quantity(inv_product_id, quantity_change)
                            inventory_dao.add_operation(inv_product_id, "in" if operation_type == "入库" else "out", inv_quantity, inv_staff_id, inv_notes)
                            st.success(f"{operation_type}操作成功！")
                            st.rerun()
                    st.markdown(f"""
                        <style>
                        [data-testid="stButton"][data-key="execute_inv_op_btn"] button {{
                            background-color: {SUCCESS_COLOR} !important;
                        }}
                        [data-testid="stButton"][data-key="execute_inv_op_btn"] button:hover {{
                            background-color: #219653 !important;
                            box-shadow: 0 2px 8px rgba(39, 174, 96, 0.3) !important;
                        }}
                        </style>
                    """, unsafe_allow_html=True)
                
                with col_btn2:
                    if st.button("清空表单", use_container_width=True, key="clear_inv_form_btn"):
                        st.rerun()
                    st.markdown(f"""
                        <style>
                        [data-testid="stButton"][data-key="clear_inv_form_btn"] button {{
                            background-color: {WARNING_COLOR} !important;
                        }}
                        [data-testid="stButton"][data-key="clear_inv_form_btn"] button:hover {{
                            background-color: #e67e22 !important;
                            box-shadow: 0 2px 8px rgba(243, 156, 18, 0.3) !important;
                        }}
                        </style>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with st.container(border=True):
                st.subheader("库存预警")
                warning_products = product_dao.get_products_below_warning_threshold(5)
                if warning_products:
                    st.warning("⚠️ 以下商品库存严重不足（≤5件），请及时补货：")
                    for p in warning_products:
                        st.write(f"• {p[0]} - {p[1]}（当前库存：{p[2]}）")
                else:
                    st.success("✅ 所有商品库存充足，无需补货")
        
        with col_list:
            with st.container(border=True):
                st.subheader("库存操作记录")
                operations = inventory_dao.get_all_operations()
                if operations:
                    op_data = []
                    for op in operations:
                        op_type = "入库" if op[3] == "in" else "出库"
                        op_data.append({
                            "操作ID": op[0],
                            "商品ID": op[1],
                            "商品名称": op[2],
                            "操作类型": op_type,
                            "操作数量": op[4],
                            "操作后库存": op[8] if op[8] else 0,
                            "操作时间": op[5],
                            "操作人员": op[6],
                            "备注": op[7] if op[7] else "无"
                        })
                    op_df = pd.DataFrame(op_data)
                    
                    def highlight_op_stock(val):
                        if val <= 5:
                            return f'background-color: #f8d7da; color: #721c24; font-weight: 500;'
                        elif val <= 30:
                            return f'background-color: #fff3cd; color: #856404; font-weight: 500;'
                        else:
                            return f'background-color: #d4edda; color: #155724; font-weight: 500;'
                    
                    st.dataframe(
                        op_df.style.applymap(highlight_op_stock, subset=["操作后库存"]),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("暂无库存操作记录，请执行库存操作！")
    
    # 报表统计标签页
    with tab4:
        st.markdown('<div class="main-title">报表统计</div>', unsafe_allow_html=True)
        
        report_type = st.radio("选择报表类型", ["销售报表", "库存报表"], horizontal=True, key="report_type_select")
        
        if st.button("生成报表", use_container_width=True, key="generate_report_btn"):
            st.markdown(f"""
                <style>
                [data-testid="stButton"][data-key="generate_report_btn"] button {{
                    background-color: {SECONDARY_COLOR} !important;
                    margin-bottom: 1rem;
                }}
                [data-testid="stButton"][data-key="generate_report_btn"] button:hover {{
                    background-color: {PRIMARY_COLOR} !important;
                    box-shadow: 0 2px 8px rgba(52, 152, 219, 0.3) !important;
                }}
                </style>
            """, unsafe_allow_html=True)
            
            if report_type == "销售报表":
                sales = sales_dao.get_all_sales()
                if not sales:
                    st.error("暂无销售数据，无法生成报表！")
                else:
                    sale_df = pd.DataFrame(sales, columns=['sale_id', 'product_id', 'product_name', 
                                                          'quantity', 'unit_price', 'total_price', 'sale_date'])
                    sale_df['sale_date'] = pd.to_datetime(sale_df['sale_date'])
                    
                    plt.close('all')
                    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
                    fig.suptitle("销售数据统计报表", fontsize=16, fontweight=600, y=0.98)
                    
                    daily_sales = sale_df.groupby(sale_df['sale_date'].dt.date)['total_price'].sum()
                    ax1.plot(daily_sales.index, daily_sales.values, marker='o', color=SECONDARY_COLOR, linewidth=2, markersize=6)
                    ax1.set_title("每日销售额趋势", fontweight=600)
                    ax1.set_xlabel("日期")
                    ax1.set_ylabel("销售额（¥）")
                    ax1.tick_params(axis='x', rotation=45)
                    ax1.grid(alpha=0.3)
                    
                    product_sales = sale_df.groupby('product_name')['quantity'].sum().sort_values(ascending=False).head(10)
                    bars = ax2.bar(product_sales.index, product_sales.values, color=SUCCESS_COLOR, alpha=0.8)
                    ax2.set_title("商品销售数量排行（TOP10）", fontweight=600)
                    ax2.set_xlabel("商品名称")
                    ax2.set_ylabel("销售数量")
                    ax2.tick_params(axis='x', rotation=45)
                    ax2.grid(alpha=0.3, axis='y')
                    for bar in bars:
                        height = bar.get_height()
                        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                                f'{int(height)}', ha='center', va='bottom', fontsize=9)
                    
                    product_revenue = sale_df.groupby('product_name')['total_price'].sum().sort_values(ascending=False).head(5)
                    colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6']
                    wedges, texts, autotexts = ax3.pie(product_revenue.values, labels=product_revenue.index, autopct='%1.1f%%', 
                                                        colors=colors, startangle=90)
                    ax3.set_title("商品销售额占比（TOP5）", fontweight=600)
                    for autotext in autotexts:
                        autotext.set_color('white')
                        autotext.set_fontweight(600)
                    
                    hourly_sales = sale_df.groupby(sale_df['sale_date'].dt.hour)['total_price'].sum()
                    bars = ax4.bar(hourly_sales.index, hourly_sales.values, color=WARNING_COLOR, alpha=0.8)
                    ax4.set_title("销售时间分布（按小时）", fontweight=600)
                    ax4.set_xlabel("小时")
                    ax4.set_ylabel("销售额（¥）")
                    ax4.grid(alpha=0.3, axis='y')
                    for bar in bars:
                        height = bar.get_height()
                        ax4.text(bar.get_x() + bar.get_width()/2., height + 5,
                                f'{int(height)}', ha='center', va='bottom', fontsize=9)
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close(fig)
                    
                    st.subheader("报表导出")
                    col_export1, col_export2 = st.columns(2, gap="small")
                    with col_export1:
                        csv_data = sale_df.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            "导出CSV格式",
                            data=csv_data,
                            file_name=f"销售报表_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            use_container_width=True,
                            key="export_sale_csv_btn"
                        )
                    with col_export2:
                        excel_buffer = io.BytesIO()
                        sale_df.to_excel(excel_buffer, index=False, engine='openpyxl')
                        excel_buffer.seek(0)
                        st.download_button(
                            "导出Excel格式",
                            data=excel_buffer,
                            file_name=f"销售报表_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            key="export_sale_excel_btn"
                        )
            
            else:
                products = product_dao.get_all_products()
                if not products:
                    st.error("暂无库存数据，无法生成报表！")
                else:
                    product_df = pd.DataFrame(products, columns=['product_id', 'name', 'price', 'quantity', 
                                                                'category', 'staff_id', 'staff_name', 'photo_path'])
                    product_df['stock_value'] = product_df['price'] * product_df['quantity']
                    
                    plt.close('all')
                    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
                    fig.suptitle("库存数据统计报表", fontsize=16, fontweight=600, y=0.98)
                    
                    category_stock = product_df.groupby('category')['quantity'].sum()
                    colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6']
                    wedges, texts, autotexts = ax1.pie(category_stock.values, labels=category_stock.index, autopct='%1.1f%%', 
                                                        colors=colors[:len(category_stock)], startangle=90)
                    ax1.set_title("库存类别分布（按数量）", fontweight=600)
                    for autotext in autotexts:
                        autotext.set_color('white')
                        autotext.set_fontweight(600)
                    
                    top_value = product_df.nlargest(5, 'stock_value')
                    bars = ax2.bar(top_value['name'], top_value['stock_value'], color=SECONDARY_COLOR, alpha=0.8)
                    ax2.set_title("商品库存价值排行（TOP5）", fontweight=600)
                    ax2.set_xlabel("商品名称")
                    ax2.set_ylabel("库存价值（¥）")
                    ax2.tick_params(axis='x', rotation=45)
                    ax2.grid(alpha=0.3, axis='y')
                    for bar in bars:
                        height = bar.get_height()
                        ax2.text(bar.get_x() + bar.get_width()/2., height + 5,
                                f'{int(height)}', ha='center', va='bottom', fontsize=9)
                    
                    top_quantity = product_df.nlargest(5, 'quantity')
                    bars = ax3.bar(top_quantity['name'], top_quantity['quantity'], color=SUCCESS_COLOR, alpha=0.8)
                    ax3.set_title("商品库存数量排行（TOP5）", fontweight=600)
                    ax3.set_xlabel("商品名称")
                    ax3.set_ylabel("库存数量")
                    ax3.tick_params(axis='x', rotation=45)
                    ax3.grid(alpha=0.3, axis='y')
                    for bar in bars:
                        height = bar.get_height()
                        ax3.text(bar.get_x() + bar.get_width()/2., height + 2,
                                f'{int(height)}', ha='center', va='bottom', fontsize=9)
                    
                    ax4.hist(product_df['price'], bins=10, edgecolor='black', color=WARNING_COLOR, alpha=0.8)
                    ax4.set_title("商品价格分布", fontweight=600)
                    ax4.set_xlabel("价格（¥）")
                    ax4.set_ylabel("商品数量")
                    ax4.grid(alpha=0.3, axis='y')
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close(fig)
                    
                    st.subheader("报表导出")
                    col_export1, col_export2 = st.columns(2, gap="small")
                    with col_export1:
                        csv_data = product_df.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            "导出CSV格式",
                            data=csv_data,
                            file_name=f"库存报表_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            use_container_width=True,
                            key="export_stock_csv_btn"
                        )
                    with col_export2:
                        excel_buffer = io.BytesIO()
                        product_df.to_excel(excel_buffer, index=False, engine='openpyxl')
                        excel_buffer.seek(0)
                        st.download_button(
                            "导出Excel格式",
                            data=excel_buffer,
                            file_name=f"库存报表_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            key="export_stock_excel_btn"
                        )
    
    st.markdown("---")
    col_logout = st.columns([10, 1])
    with col_logout[1]:
        st.markdown('<div class="danger-btn">', unsafe_allow_html=True)
        if st.button("退出登录", use_container_width=True, key="logout_btn"):
            # 退出登录时，清空URL参数（新版API：直接清空st.query_params）
            st.query_params.clear()  # 清空所有URL参数
            st.session_state.logged_in = False
            st.session_state.user_info = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ===================== 程序入口 =====================
if __name__ == "__main__":
    if not st.session_state.logged_in:
        login_page()
    else:
        main_system()
