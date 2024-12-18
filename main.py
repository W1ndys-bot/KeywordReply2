# script/KeywordReply2/main.py

import logging
import os
import re
import sys

# 添加项目根目录到sys.path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.config import owner_id
from app.api import *
from app.switch import load_switch, save_switch

# 数据存储路径，实际开发时，请将KeywordReply2替换为具体的数据存放路径
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "KeywordReply2",
)


# 查看功能开关状态
def load_function_status(group_id):
    try:
        return load_switch(group_id, "KeywordReply2")
    except Exception as e:
        logging.error(f"加载功能开关状态失败: {e}")
        return False


# 保存功能开关状态
def save_function_status(group_id, status):
    try:
        save_switch(group_id, "KeywordReply2", status)
    except Exception as e:
        logging.error(f"保存功能开关状态失败: {e}")


# 初始化词库db文件，键为关键词，值为回复内容
def init_keyword_reply_db():
    try:
        db_path = os.path.join(DATA_DIR, "keyword_reply.db")
        if not os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # 创建关键词回复表，关键词设为唯一值
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS keyword_replies (
                    keyword TEXT PRIMARY KEY,
                    reply TEXT NOT NULL
                )
            """
            )
            conn.commit()
            conn.close()
            logging.info(f"初始化词库数据库成功")
    except Exception as e:
        logging.error(f"初始化词库数据库失败: {e}")


# 初始化群号db文件，只存储一列，列名为group_id，值为群号
def init_group_db():
    try:
        group_db_path = os.path.join(DATA_DIR, f"groups.db")
        if not os.path.exists(group_db_path):
            conn = sqlite3.connect(group_db_path)
            cursor = conn.cursor()
            # 创建群号表
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS groups (
                    group_id TEXT PRIMARY KEY
                )
            """
            )
            conn.commit()
            conn.close()
            logging.info(f"初始化群号数据库成功")
    except Exception as e:
        logging.error(f"初始化群号数据库失败: {e}")


# 初始化
async def init_KeywordReply2():
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    init_keyword_reply_db()
    init_group_db()


# 更新关键词回复
async def update_keyword_reply(keyword, reply):
    try:
        db_path = os.path.join(DATA_DIR, "keyword_reply.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # 使用INSERT OR REPLACE语句，如果关键词存在则更新，不存在则插入
        cursor.execute(
            "INSERT OR REPLACE INTO keyword_replies (keyword, reply) VALUES (?, ?)",
            (keyword, reply),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"更新关键词回复失败: {e}")
        raise


# 删除关键词回复
async def delete_keyword_reply(keyword):
    try:
        db_path = os.path.join(DATA_DIR, "keyword_reply.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM keyword_replies WHERE keyword = ?", (keyword,))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"删除关键词回复失败: {e}")
        raise


# 新增开启的群号
async def add_group(group_id):
    try:
        db_path = os.path.join(DATA_DIR, "groups.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO groups (group_id) VALUES (?)", (group_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"新增群号失败: {e}")
        raise


# 删除开启的群号
async def delete_group(group_id):
    try:
        db_path = os.path.join(DATA_DIR, "groups.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM groups WHERE group_id = ?", (group_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"删除群号失败: {e}")
        raise


# 获取关键词回复
async def get_keyword_reply(keyword):
    try:
        db_path = os.path.join(DATA_DIR, "keyword_reply.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT reply FROM keyword_replies WHERE keyword = ?", (keyword,)
        )
        reply = cursor.fetchone()
        conn.close()
        return reply[0] if reply else None
    except Exception as e:
        logging.error(f"获取关键词回复失败: {e}")
        return None


# 获取群号
async def get_groups():
    try:
        db_path = os.path.join(DATA_DIR, "groups.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT group_id FROM groups")
        groups = cursor.fetchall()
        conn.close()
        return groups
    except Exception as e:
        logging.error(f"获取群号列表失败: {e}")
        return []


# 处理关键词回复
async def handle_keyword_reply(msg, group_id, message_id):

    # 检查群号是否开启
    if not await load_function_status(group_id):
        return

    # 获取关键词
    keyword = str(msg.get("raw_message"))

    # 获取回复内容
    reply = await get_keyword_reply(keyword)

    reply = f"[CQ:reply,id={message_id}]{reply}"
    # 发送回复
    await send_group_msg(group_id, reply)


# 管理函数
async def manage_KeywordReply2(group_id, raw_message):
    # 解析命令
    match = re.match("kr2add(.*) (.*)", raw_message) or re.match(
        "添加关键词(.*) (.*)", raw_message
    )
    if match:
        keyword = match.group(1)
        reply = match.group(2)
        await update_keyword_reply(keyword, reply)
        await send_group_msg(
            group_id, "添加成功，关键词：" + keyword + "，回复：" + reply
        )
        return

    match = re.match("kr2del(.*)", raw_message) or re.match(
        "删除关键词(.*)", raw_message
    )
    if match:
        keyword = match.group(1)
        await delete_keyword_reply(keyword)
        await send_group_msg(group_id, "删除成功，关键词：" + keyword)
        return

    match = re.match("kr2addgroup(.*)", raw_message) or re.match(
        "添加群号(.*)", raw_message
    )
    if match:
        group_id = match.group(1)
        await add_group(group_id)
        await send_group_msg(group_id, "添加成功，群号：" + group_id)
        return

    match = re.match("kr2delgroup(.*)", raw_message) or re.match(
        "删除群号(.*)", raw_message
    )
    if match:
        group_id = match.group(1)
        await delete_group(group_id)
        await send_group_msg(group_id, "删除成功，群号：" + group_id)
        return

    match = re.match("kr2listgroup", raw_message) or re.match("查看群号", raw_message)
    if match:
        groups = await get_groups()
        group_list = "\n".join([group[0] for group in groups])
        await send_group_msg(group_id, "群号列表：\n" + group_list)
        return


# 群消息处理函数
async def handle_KeywordReply2_group_message(websocket, msg):
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        user_id = str(msg.get("user_id"))
        group_id = str(msg.get("group_id"))
        raw_message = str(msg.get("raw_message"))
        role = str(msg.get("sender", {}).get("role"))
        message_id = str(msg.get("message_id"))

        # 初始化
        await init_KeywordReply2()

        # 判断是否有权限
        authorized = is_authorized(role, user_id)

        # 如果有权限，可以进行管理
        if authorized:
            # 管理
            await manage_KeywordReply2(group_id, raw_message)
        else:
            # 处理关键词回复
            await handle_keyword_reply(msg, group_id, message_id)

    except Exception as e:
        logging.error(f"处理KeywordReply2群消息失败: {e}")
        return
