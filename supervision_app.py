import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd

# ======================== 全局配置 ========================
st.set_page_config(page_title="大监督体系", page_icon="📋", layout="wide")

# 账号密码配置
USER_CRED = {"username": "123456", "password": "123456"}
ADMIN_CRED = {"username": "999999", "password": "999999"}

# 检查类型映射
CHECK_TYPES = {
    1: {"name": "纪检检查", "table": "discipline_check"},
    2: {"name": "风险检查", "table": "risk_check"},
    3: {"name": "合规检查", "table": "compliance_check"},
    4: {"name": "审计检查", "table": "audit_check"},
    5: {"name": "财务检查", "table": "finance_check"},
    6: {"name": "其他检查", "table": "other_check"}
}

# 问题类型/严重程度配置
PROBLEM_TYPE_RATIO = {"重大违规": 1.0, "严重违规": 0.8, "一般违规": 0.5, "轻微问题": 0.2}
SEVERITY_CONFIG = {"高": {"score": 20, "work_days": 15}, "中": {"score": 10, "work_days": 10}, "低": {"score": 5, "work_days": 5}}

# ======================== 工具函数 ========================
def init_db():
    """初始化数据库和表"""
    conn = sqlite3.connect('supervision_system.db')
    cursor = conn.cursor()
    
    # 创建6张检查表
    create_table_sql = """
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            机构编码 TEXT NOT NULL,
            机构名称 TEXT NOT NULL,
            检查日期 TEXT NOT NULL,
            问题类型 TEXT NOT NULL,
            问题描述 TEXT NOT NULL,
            严重程度 TEXT NOT NULL,
            问题分值 INTEGER NOT NULL,
            标准扣分 REAL NOT NULL,
            整改要求 TEXT NOT NULL,
            整改期限 TEXT NOT NULL,
            责任部门 TEXT NOT NULL,
            责任人 TEXT NOT NULL,
            整改状态 TEXT NOT NULL,
            验证人 TEXT NOT NULL,
            备注 TEXT,
            提交时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    for _, info in CHECK_TYPES.items():
        cursor.execute(create_table_sql.format(table_name=info["table"]))
    
    conn.commit()
    conn.close()

def add_work_days(start_date, days):
    """计算工作日（跳过周末）"""
    current_date = start_date
    added_days = 0
    while added_days < days:
        current_date += timedelta(days=1)
        if current_date.weekday() < 5:  # 0=周一，6=周日
            added_days += 1
    return current_date

def save_data(table_name, data):
    """保存数据到数据库"""
    conn = sqlite3.connect('supervision_system.db')
    cursor = conn.cursor()
    
    insert_sql = f"""
        INSERT INTO {table_name} (
            机构编码, 机构名称, 检查日期, 问题类型, 问题描述, 严重程度,
            问题分值, 标准扣分, 整改要求, 整改期限, 责任部门, 责任人,
            整改状态, 验证人, 备注
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    cursor.execute(insert_sql, (
        data["org_code"], data["org_name"], data["check_date_str"],
        data["problem_type"], data["problem_desc"], data["severity"],
        data["problem_score"], data["standard_deduction"], data["rectification_req"],
        data["rectification_date_str"], data["dept"], data["responsible_person"],
        data["rectification_status"], data["verifier"], data["remark"]
    ))
    
    conn.commit()
    conn.close()

def get_table_data(table_name):
    """获取指定表的所有数据"""
    conn = sqlite3.connect('supervision_system.db')
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df

# ======================== 页面逻辑 ========================
def login_page():
    """登录页面"""
    st.title("📋 大监督体系 - 登录")
    st.divider()
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        username = st.text_input("账号", placeholder="请输入账号")
        password = st.text_input("密码", type="password", placeholder="请输入密码")
        
        if st.button("登录", use_container_width=True):
            if username == USER_CRED["username"] and password == USER_CRED["password"]:
                st.session_state["role"] = "user"
                st.session_state["logged_in"] = True
                st.rerun()  # 刷新页面
            elif username == ADMIN_CRED["username"] and password == ADMIN_CRED["password"]:
                st.session_state["role"] = "admin"
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("账号或密码错误，请重试！")

def user_page():
    """用户填报页面"""
    st.title("📋 大监督体系 - 问题填报")
    st.divider()
    
    # 步骤1：选择检查类型
    st.subheader("步骤1：选择检查类型")
    check_type_key = st.selectbox(
        "请选择检查类型",
        options=list(CHECK_TYPES.keys()),
        format_func=lambda x: CHECK_TYPES[x]["name"],
        key="check_type"
    )
    check_type = CHECK_TYPES[check_type_key]
    st.info(f"当前选择：{check_type['name']}")
    
    # 步骤2：填写基础信息
    st.subheader("步骤2：填写基础信息")
    col1, col2 = st.columns(2)
    
    with col1:
        org_code = st.text_input("机构编码 *", placeholder="如：001", key="org_code")
        org_name = st.text_input("机构名称 *", placeholder="如：总行财务部", key="org_name")
        check_date = st.date_input("检查日期 *", key="check_date")
        problem_type = st.selectbox(
            "问题类型 *",
            options=["重大违规", "严重违规", "一般违规", "轻微问题"],
            key="problem_type"
        )
        problem_desc = st.text_area("问题描述 *", placeholder="请详细描述发现的问题", key="problem_desc")
    
    with col2:
        severity = st.selectbox(
            "严重程度 *",
            options=["高", "中", "低"],
            key="severity"
        )
        dept = st.text_input("责任部门 *", placeholder="如：财务部", key="dept")
        responsible_person = st.text_input("责任人 *", placeholder="如：张三", key="responsible_person")
        rectification_status = st.selectbox(
            "整改状态 *",
            options=["未整改", "整改中", "已整改", "整改未通过"],
            key="rect_status"
        )
        verifier = st.text_input("验证人 *", placeholder="如：李四", key="verifier")
        remark = st.text_area("备注（可选）", placeholder="填写补充说明", key="remark")
    
    # 自动计算字段（实时展示）
    st.subheader("步骤3：自动生成信息（无需填写）")
    col_auto1, col_auto2, col_auto3, col_auto4 = st.columns(4)
    
    # 计算问题分值
    problem_score = SEVERITY_CONFIG[severity]["score"]
    with col_auto1:
        st.metric("问题分值", problem_score)
    
    # 计算标准扣分
    standard_deduction = problem_score * PROBLEM_TYPE_RATIO[problem_type]
    with col_auto2:
        st.metric("标准扣分", f"{standard_deduction:.2f}")
    
    # 计算整改要求
    if problem_score >= 8:
        rectification_req = "限期整改，并提交整改报告"
    elif 5 <= problem_score < 8:
        rectification_req = "限期整改"
    else:
        rectification_req = "口头警告，立即整改"
    with col_auto3:
        st.metric("整改要求", rectification_req)
    
    # 计算整改期限
    work_days = SEVERITY_CONFIG[severity]["work_days"]
    rectification_date = add_work_days(check_date, work_days)
    rectification_date_str = rectification_date.strftime("%Y-%m-%d")
    with col_auto4:
        st.metric("整改期限", f"{rectification_date_str}（+{work_days}个工作日）")
    
    # 提交按钮
    st.divider()
    submit_btn = st.button("提交数据", use_container_width=True, type="primary")
    
    if submit_btn:
        # 校验必填项
        if not all([org_code, org_name, problem_desc, dept, responsible_person, verifier]):
            st.error("⚠️ 带*的字段为必填项，请补充完整！")
        else:
            # 组装数据并保存
            data = {
                "org_code": org_code,
                "org_name": org_name,
                "check_date_str": check_date.strftime("%Y-%m-%d"),
                "problem_type": problem_type,
                "problem_desc": problem_desc,
                "severity": severity,
                "problem_score": problem_score,
                "standard_deduction": standard_deduction,
                "rectification_req": rectification_req,
                "rectification_date_str": rectification_date_str,
                "dept": dept,
                "responsible_person": responsible_person,
                "rectification_status": rectification_status,
                "verifier": verifier,
                "remark": remark
            }
            
            save_data(check_type["table"], data)
            st.success("✅ 数据提交成功！所有信息已保存到数据库。")
            
            # 展示提交的数据
            st.subheader("提交的信息预览")
            st.dataframe(pd.DataFrame([data]), use_container_width=True)

def admin_page():
    """管理员查看数据页面"""
    st.title("📋 大监督体系 - 管理员数据查看")
    st.divider()
    
    # 选择要查看的表
    selected_table_key = st.selectbox(
        "选择要查看的检查表",
        options=list(CHECK_TYPES.keys()),
        format_func=lambda x: CHECK_TYPES[x]["name"],
        key="admin_table"
    )
    selected_table = CHECK_TYPES[selected_table_key]
    
    # 加载并展示数据
    st.subheader(f"{selected_table['name']} 数据")
    df = get_table_data(selected_table["table"])
    
    if df.empty:
        st.warning("📄 该检查表暂无数据！")
    else:
        # 格式化数值列
        df["标准扣分"] = df["标准扣分"].round(2)
        # 展示数据表格
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # 可选：下载数据为Excel
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="下载数据为CSV文件",
            data=csv,
            file_name=f"{selected_table['name']}_数据.csv",
            mime="text/csv",
            use_container_width=True
        )

# ======================== 主程序 ========================
def main():
    # 初始化数据库
    init_db()
    
    # 初始化session状态（记录登录状态）
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state["role"] = ""
    
    # 未登录时显示登录页
    if not st.session_state["logged_in"]:
        login_page()
    else:
        # 已登录：显示退出按钮
        if st.sidebar.button("退出登录", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["role"] = ""
            st.rerun()
        
        # 根据角色显示对应页面
        if st.session_state["role"] == "user":
            user_page()
        elif st.session_state["role"] == "admin":
            admin_page()

if __name__ == "__main__":
    main()
