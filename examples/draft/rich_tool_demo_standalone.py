"""
Rich Tool 完整使用演示 - 独立版本
展示所有可用的打印功能和样式选项
"""

import time

# 直接导入 rich_tool 模块
from menglong.utils.log import rich_tool


def demo_basic_messages():
    """演示基本消息类型"""
    rich_tool.print_header("基本消息类型演示", "展示不同类型的日志消息")

    rich_tool.success("操作成功完成")
    rich_tool.error("发生了一个错误")
    rich_tool.warning("这是一个警告信息")
    rich_tool.info("这是一般信息")
    rich_tool.debug("这是调试信息")
    rich_tool.system("系统级别消息")
    rich_tool.user("用户相关消息")
    rich_tool.agent("AI智能体消息")
    rich_tool.tool("工具执行消息")

    rich_tool.print_separator()


def demo_message_options():
    """演示消息选项"""
    rich_tool.print_rule("消息选项演示", "cyan")

    # 带标题的消息
    rich_tool.success("这是带标题的成功消息", title="成功")
    rich_tool.error("这是带标题的错误消息", title="错误")

    # 带时间戳的消息
    rich_tool.info("这是带时间戳的消息", timestamp=True)
    rich_tool.warning("警告消息也可以带时间戳", timestamp=True)

    # 面板样式的消息
    rich_tool.success("这是面板样式的成功消息", panel=True, title="重要成功")
    rich_tool.error(
        "这是面板样式的错误消息", panel=True, title="严重错误", timestamp=True
    )

    rich_tool.print_separator()


def demo_data_display():
    """演示数据显示功能"""
    rich_tool.print_rule("数据显示演示", "blue")

    # JSON 数据演示
    user_data = {
        "name": "张三",
        "age": 28,
        "email": "zhangsan@example.com",
        "skills": ["Python", "JavaScript", "Docker"],
        "profile": {
            "department": "技术部",
            "position": "高级工程师",
            "experience": "5年",
        },
    }

    rich_tool.print_json(user_data, "用户详细信息", sort_keys=True)

    # 字典数据（简化版）
    config_data = {
        "database_url": "postgresql://localhost:5432/mydb",
        "redis_url": "redis://localhost:6379",
        "debug": True,
        "log_level": "INFO",
    }

    rich_tool.print_dict(config_data, "应用配置")

    rich_tool.print_separator()


def demo_table_display():
    """演示表格显示功能"""
    rich_tool.print_rule("表格显示演示", "green")

    # 员工信息表
    employees = [
        {
            "姓名": "张三",
            "年龄": 28,
            "部门": "技术部",
            "职位": "高级工程师",
            "状态": "在线",
        },
        {
            "姓名": "李四",
            "年龄": 32,
            "部门": "产品部",
            "职位": "产品经理",
            "状态": "会议中",
        },
        {
            "姓名": "王五",
            "年龄": 26,
            "部门": "设计部",
            "职位": "UI设计师",
            "状态": "离线",
        },
        {
            "姓名": "赵六",
            "年龄": 30,
            "部门": "技术部",
            "职位": "架构师",
            "状态": "在线",
        },
    ]

    rich_tool.print_table(employees, title="员工信息表", show_lines=True)

    # 简单列表
    todo_list = [
        "完成用户认证模块",
        "实现数据导入功能",
        "编写API文档",
        "进行性能测试",
        "部署到生产环境",
    ]

    rich_tool.print_list(todo_list, "待办事项")

    rich_tool.print_separator()


def demo_tree_structure():
    """演示树形结构显示"""
    rich_tool.print_rule("树形结构演示", "purple")

    # 项目目录结构
    project_structure = {
        "my_project": {
            "src": {
                "components": ["Header.vue", "Sidebar.vue", "Content.vue"],
                "utils": ["api.js", "helpers.js", "validators.js"],
                "styles": ["main.css", "variables.css"],
            },
            "tests": {"unit": ["user.test.js", "api.test.js"], "e2e": ["app.test.js"]},
            "docs": {"api": "API文档", "user_guide": "用户指南"},
        }
    }

    rich_tool.print_tree(project_structure, "项目目录结构", "bright_blue")

    rich_tool.print_separator()


def demo_markdown_content():
    """演示 Markdown 内容显示"""
    rich_tool.print_rule("Markdown 内容演示", "bright_green")

    # 项目文档
    readme_content = """
# 项目说明

这是一个功能强大的 **Web 应用程序**，提供以下特性：

## 主要功能

### 用户管理
- 用户注册和登录
- 权限控制
- 个人资料管理

### 数据处理
- 数据导入导出
- 实时数据分析
- 报表生成

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.9+ | 后端开发 |
| Vue.js | 3.0 | 前端框架 |
| PostgreSQL | 13+ | 数据库 |

## 快速开始

```bash
git clone https://github.com/example/project.git
cd project
pip install -r requirements.txt
python manage.py runserver
```

> 注意：确保 Python 版本 >= 3.9
"""

    rich_tool.print_markdown(readme_content, "项目 README")

    rich_tool.print_separator()


def demo_panels_and_layout():
    """演示面板和布局功能"""
    rich_tool.print_rule("面板和布局演示", "magenta")

    # 不同样式的面板
    rich_tool.print_panel(
        "这是一个信息面板\n用于显示重要信息\n支持多行内容",
        title="信息面板",
        style="blue",
        padding=2,
    )

    rich_tool.print_panel(
        "这是一个警告面板\n请注意相关事项\n确保操作安全",
        title="警告",
        style="yellow",
        width=60,
    )

    # 居中内容
    rich_tool.print_center("居中显示的标题", "bold bright_blue")
    rich_tool.print_center("居中显示的副标题", "dim italic")

    # 不同样式的分隔线
    rich_tool.print_rule("蓝色分隔线", "blue")
    rich_tool.print_rule("绿色分隔线", "green")
    rich_tool.print_rule("黄色分隔线", "yellow")

    # 不同字符的分隔符
    rich_tool.print_separator("=", 50, "cyan")
    rich_tool.print_separator("-", 40, "yellow")
    rich_tool.print_separator("*", 30, "green")

    rich_tool.print_separator()


def demo_interactive_features():
    """演示交互功能"""
    rich_tool.print_rule("交互功能演示", "bright_cyan")

    # 状态指示器演示
    rich_tool.info("开始演示状态指示器...")

    with rich_tool.print_status("正在初始化系统...") as status:
        time.sleep(1)
        status.update("正在加载配置...")
        time.sleep(1)
        status.update("正在启动服务...")
        time.sleep(1)

    rich_tool.success("系统初始化完成!")

    # 进度条演示
    rich_tool.info("开始演示进度条...")

    def print_progress_demo() -> None:
        """演示进度条功能"""
        import time

        with rich_tool.Progress(console=rich_tool.console) as progress:
            task = progress.add_task("[cyan]处理中...", total=100)

            while not progress.finished:
                progress.update(task, advance=10)
                time.sleep(0.1)

    print_progress_demo()

    rich_tool.print_separator()


def demo_generate_feature():
    """演示 print_generate 功能"""
    rich_tool.print_rule("生成器演示", "purple")

    # 演示1：简单列表生成器
    rich_tool.info("演示1: 处理简单列表")
    simple_list = ["文件1.txt", "文件2.py", "文件3.md", "文件4.json", "文件5.csv"]
    results = rich_tool.print_generate(simple_list, title="处理文件列表", style="green")
    rich_tool.success(f"处理完成，共 {len(results)} 个文件")

    print()

    # 演示2：数字生成器
    rich_tool.info("演示2: 数字序列生成")
    number_gen = (f"处理数据块 {i}" for i in range(1, 8))
    results = rich_tool.print_generate(
        number_gen, title="数据处理序列", show_progress=True, style="cyan"
    )

    print()

    # 演示3：不显示进度的简洁模式
    rich_tool.info("演示3: 简洁模式（无进度）")
    tasks = ["初始化配置", "连接数据库", "加载模块", "启动服务"]
    rich_tool.print_generate(
        tasks, title="系统启动步骤", show_progress=False, style="yellow"
    )

    rich_tool.print_separator()


def demo_progress_feature():
    """演示 print_progress 功能"""
    rich_tool.print_rule("多任务进度演示", "bright_magenta")

    # 演示1：基本进度显示
    rich_tool.info("演示1: 基本多任务进度")
    tasks = [
        {"name": "下载文件", "total": 100, "completed": 85},
        {"name": "解压文件", "total": 50, "completed": 50},
        {"name": "安装依赖", "total": 30, "completed": 15},
        {"name": "配置环境", "total": 20, "completed": 0},
    ]

    rich_tool.print_progress(tasks, title="安装进度", show_details=True)

    print()

    # 演示2：实时进度更新模拟
    rich_tool.info("演示2: 模拟实时进度更新")

    # 模拟3个阶段的进度更新
    for stage in range(1, 4):
        rich_tool.info(f"阶段 {stage} 进度更新")

        if stage == 1:
            stage_tasks = [
                {"name": "数据预处理", "total": 100, "completed": 25},
                {"name": "模型训练", "total": 100, "completed": 0},
                {"name": "结果评估", "total": 100, "completed": 0},
            ]
        elif stage == 2:
            stage_tasks = [
                {"name": "数据预处理", "total": 100, "completed": 100},
                {"name": "模型训练", "total": 100, "completed": 60},
                {"name": "结果评估", "total": 100, "completed": 0},
            ]
        else:
            stage_tasks = [
                {"name": "数据预处理", "total": 100, "completed": 100},
                {"name": "模型训练", "total": 100, "completed": 100},
                {"name": "结果评估", "total": 100, "completed": 100},
            ]

        rich_tool.print_progress(stage_tasks, show_details=False)

        if stage < 3:
            time.sleep(1)  # 模拟时间间隔

    rich_tool.success("所有任务完成！")

    print()

    # 演示3：项目开发进度
    rich_tool.info("演示3: 项目开发进度跟踪")
    project_tasks = [
        {"name": "需求分析", "total": 10, "completed": 10},
        {"name": "系统设计", "total": 15, "completed": 15},
        {"name": "前端开发", "total": 40, "completed": 35},
        {"name": "后端开发", "total": 50, "completed": 42},
        {"name": "测试验证", "total": 20, "completed": 8},
        {"name": "部署上线", "total": 10, "completed": 0},
    ]

    rich_tool.print_progress(project_tasks, title="项目开发进度", show_details=True)

    rich_tool.print_separator()


def demo_advanced_interactive():
    """演示高级交互功能"""
    rich_tool.print_rule("高级交互功能演示", "bright_red")

    # 综合演示：文件处理流程
    rich_tool.print_header("文件批处理演示", "结合 generate 和 progress 功能")

    # 步骤1：文件发现
    rich_tool.info("步骤1: 发现待处理文件")
    files = [
        "data/users.csv",
        "data/orders.json",
        "data/products.xml",
        "data/logs.txt",
        "data/config.yaml",
    ]

    discovered_files = rich_tool.print_generate(files, title="文件发现", style="blue")

    print()

    # 步骤2：文件处理进度
    rich_tool.info("步骤2: 文件处理进度")

    # 模拟处理过程
    for step in ["开始处理", "处理中", "即将完成"]:
        rich_tool.info(f"当前状态: {step}")

        if step == "开始处理":
            file_progress = [
                {"name": "users.csv", "total": 1000, "completed": 100},
                {"name": "orders.json", "total": 500, "completed": 0},
                {"name": "products.xml", "total": 300, "completed": 0},
                {"name": "logs.txt", "total": 2000, "completed": 0},
                {"name": "config.yaml", "total": 50, "completed": 0},
            ]
        elif step == "处理中":
            file_progress = [
                {"name": "users.csv", "total": 1000, "completed": 1000},
                {"name": "orders.json", "total": 500, "completed": 350},
                {"name": "products.xml", "total": 300, "completed": 200},
                {"name": "logs.txt", "total": 2000, "completed": 800},
                {"name": "config.yaml", "total": 50, "completed": 30},
            ]
        else:  # 即将完成
            file_progress = [
                {"name": "users.csv", "total": 1000, "completed": 1000},
                {"name": "orders.json", "total": 500, "completed": 500},
                {"name": "products.xml", "total": 300, "completed": 300},
                {"name": "logs.txt", "total": 2000, "completed": 2000},
                {"name": "config.yaml", "total": 50, "completed": 50},
            ]

        rich_tool.print_progress(file_progress, title="文件处理进度")

        if step != "即将完成":
            time.sleep(1)

    # 步骤3：结果汇总
    rich_tool.info("步骤3: 处理结果汇总")

    results = [
        "用户数据: 1000 条记录已处理",
        "订单数据: 500 条记录已处理",
        "产品数据: 300 条记录已处理",
        "日志数据: 2000 行已分析",
        "配置文件: 已更新",
    ]

    rich_tool.print_generate(
        results, title="处理结果", show_progress=False, style="green"
    )

    rich_tool.success("文件批处理完成！", panel=True, title="处理完成")

    rich_tool.print_separator()


def main():
    """主演示函数"""
    rich_tool.print_header(
        "Rich Tool 完整功能演示", "展示所有美观的打印功能和实际应用场景"
    )

    try:
        # 基础功能演示
        demo_basic_messages()
        demo_message_options()

        # 数据显示功能
        demo_data_display()
        demo_table_display()
        demo_tree_structure()

        # 内容格式化
        demo_markdown_content()
        demo_panels_and_layout()

        # 交互功能
        demo_interactive_features()

        # 生成和进度演示
        demo_generate_feature()
        demo_progress_feature()

        # 高级交互功能演示
        demo_advanced_interactive()

        # 演示结束
        rich_tool.print_footer("演示完成！感谢观看")

        # 使用说明
        usage_guide = """
## Rich Tool 使用指南

### 基本用法

```python
# 导入模块
from menglong.utils.log.rich_tool import *

# 基本消息
success("操作成功")
error("出现错误") 
warning("警告信息")
info("一般信息")

# 面板消息
success("重要成功", panel=True, title="成功")
error("严重错误", panel=True, timestamp=True)

# 数据显示
data = {"key": "value"}
print_json(data, "JSON数据")

table_data = [{"名称": "张三", "年龄": 25}]
print_table(table_data, "表格数据")

# 面板和布局
print_panel("重要内容", title="标题", style="green")
print_center("居中文本", "bold")
print_rule("分隔线", "blue")
```

### 高级功能

- `print_tree()` - 显示树形结构
- `print_markdown()` - 渲染 Markdown 内容  
- `print_status()` - 显示动态状态
- `print_progress_demo()` - 进度条演示
- `print_generate()` - 生成器内容展示，支持进度显示
- `print_progress()` - 多任务进度跟踪和可视化

### 新增功能详细说明

#### print_generate 示例

```python
# 处理列表并显示进度
files = ["file1.txt", "file2.py", "file3.md"]
results = print_generate(files, title="处理文件", style="green")

# 处理生成器（无长度）
data_gen = (f"数据 {i}" for i in range(10))
print_generate(data_gen, title="数据处理", show_progress=True)

# 简洁模式（不显示进度）
tasks = ["初始化", "连接", "启动"]
print_generate(tasks, show_progress=False, style="yellow")
```

#### print_progress 示例

```python
# 多任务进度显示
tasks = [
    {"name": "下载文件", "total": 100, "completed": 75},
    {"name": "安装依赖", "total": 50, "completed": 30},
    {"name": "配置环境", "total": 20, "completed": 20},
]
print_progress(tasks, title="安装进度", show_details=True)

# 简单进度显示
print_progress(tasks, show_details=False)
```

更多详细信息请参考源代码注释。
"""

        rich_tool.print_markdown(usage_guide, "使用指南")

    except Exception as e:
        rich_tool.error(f"演示过程中发生错误: {e}")
        import traceback

        rich_tool.debug(traceback.format_exc())


if __name__ == "__main__":
    main()
