"""
测试MengLong包安装和基本导入功能

运行方法:
    python test/test_installation.py
"""

import sys
import importlib.util


def test_package_installed():
    """验证MengLong包已正确安装"""
    try:
        # 尝试导入mlong包
        import mlong

        print("✅ mlong包已成功安装")
        print(f"✅ 版本: {getattr(mlong, '__version__', '未定义')}")
        print(f"✅ 包位置: {mlong.__file__}")
        return True
    except ImportError as e:
        print(f"❌ 导入mlong包失败: {e}")
        return False


def test_submodules():
    """测试关键子模块是否可以正确导入"""
    modules_to_test = ["mlong.agent", "mlong.memory", "mlong.model_interface"]

    all_success = True
    for module_name in modules_to_test:
        try:
            module = importlib.import_module(module_name)
            print(f"✅ 成功导入模块: {module_name}")
        except ImportError as e:
            print(f"❌ 导入模块失败 {module_name}: {e}")
            all_success = False

    return all_success


if __name__ == "__main__":
    print("开始测试MengLong包安装...\n")

    package_installed = test_package_installed()
    if package_installed:
        print("\n测试子模块导入...")
        submodules_ok = test_submodules()

        if submodules_ok:
            print("\n✅ 所有测试通过！MengLong已正确安装。")
            sys.exit(0)
        else:
            print("\n⚠️ 包已安装但某些子模块导入失败，请检查安装是否完整。")
            sys.exit(1)
    else:
        print("\n❌ MengLong包未正确安装。请检查安装步骤。")
        sys.exit(1)
