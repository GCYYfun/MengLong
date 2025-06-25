"""
监控配置使用示例

展示如何通过配置文件、环境变量或代码来配置监控行为。
"""

import os
from menglong.monitor import (
    init_monitoring,
    get_config,
    create_default_config,
    enable_debug_monitoring,
    enable_production_monitoring,
    enable_tool_debugging,
    enable_model_debugging,
    log_model_interaction,
    log_tool_call,
    get_monitor,
)


def demonstrate_config_file():
    """演示通过配置文件控制监控"""

    print("=== 通过配置文件控制监控 ===\n")

    # 1. 创建默认配置文件
    create_default_config("demo_monitor_config.yaml")

    # 2. 通过配置文件初始化监控
    init_monitoring("demo_monitor_config.yaml")

    # 3. 查看配置状态
    config = get_config()
    print(f"当前配置: {config.get_config()}")

    # 4. 测试监控
    log_model_interaction("配置文件测试", model_id="test")
    log_tool_call("test_tool", arguments={"test": "value"})

    print(f"监控状态: {get_monitor().get_status()}")


def demonstrate_env_config():
    """演示通过环境变量控制监控"""

    print("\n=== 通过环境变量控制监控 ===\n")

    # 设置环境变量
    os.environ["ML_MONITOR_ENABLED"] = "true"
    os.environ["ML_MONITOR_LEVEL"] = "DEBUG"
    os.environ["ML_MONITOR_CATEGORIES"] = "MODEL_INTERACTION,TOOL_CALLS"

    # 重新初始化监控
    init_monitoring()

    # 测试监控
    log_model_interaction("环境变量测试", model_id="test")
    log_tool_call("env_tool", arguments={"env": "test"})

    print(f"监控状态: {get_monitor().get_status()}")

    # 清理环境变量
    for key in ["ML_MONITOR_ENABLED", "ML_MONITOR_LEVEL", "ML_MONITOR_CATEGORIES"]:
        if key in os.environ:
            del os.environ[key]


def demonstrate_preset_configs():
    """演示预设配置"""

    print("\n=== 预设配置演示 ===\n")

    # 调试配置
    print("1. 启用调试配置...")
    enable_debug_monitoring()
    log_model_interaction("调试模式测试", model_id="debug")
    print(f"调试模式状态: {get_monitor().get_status()}")

    print("\n2. 启用生产配置...")
    enable_production_monitoring()
    log_model_interaction(
        "生产模式测试", level="ERROR", model_id="prod"
    )  # 只有ERROR级别会显示
    log_model_interaction("生产模式测试", level="INFO", model_id="prod")  # 这个不会显示
    print(f"生产模式状态: {get_monitor().get_status()}")

    print("\n3. 启用工具调试配置...")
    enable_tool_debugging()
    log_tool_call("debug_tool", arguments={"debug": True})
    log_model_interaction("这个不会显示", model_id="test")  # 不在启用的分类中
    print(f"工具调试状态: {get_monitor().get_status()}")

    print("\n4. 启用模型调试配置...")
    enable_model_debugging()
    log_model_interaction("模型调试测试", model_id="model_debug")
    log_tool_call(tool_name="test")  # 不在启用的分类中
    print(f"模型调试状态: {get_monitor().get_status()}")


def demonstrate_dynamic_config():
    """演示动态配置更新"""

    print("\n=== 动态配置更新演示 ===\n")

    config = get_config()

    # 1. 运行时更新配置
    print("1. 更新配置启用所有监控...")
    config.update_config(
        {
            "monitor": {
                "enabled": True,
                "level": "DEBUG",
                "categories": [
                    "MODEL_INTERACTION",
                    "TOOL_CALLS",
                    "PERFORMANCE",
                    "ERROR_TRACKING",
                ],
            }
        }
    )
    config.apply_config()

    log_model_interaction("动态配置测试1", model_id="dynamic")
    log_tool_call("dynamic_tool", arguments={"test": 1})

    # 2. 运行时禁用某些分类
    print("\n2. 运行时禁用工具调用监控...")
    config.update_config(
        {"monitor": {"categories": ["MODEL_INTERACTION", "ERROR_TRACKING"]}}
    )
    config.apply_config()

    log_model_interaction("这个会显示", model_id="dynamic")
    log_tool_call(tool_name="dynamic_tool")

    # 3. 运行时调整级别
    print("\n3. 运行时调整到ERROR级别...")
    config.update_config({"monitor": {"level": "ERROR"}})
    config.apply_config()

    log_model_interaction("这个不会显示 (INFO)", model_id="dynamic")
    log_model_interaction("这个会显示 (ERROR)", level="ERROR", model_id="dynamic")

    print(f"最终配置状态: {get_monitor().get_status()}")


def demonstrate_config_scenarios():
    """演示不同场景的配置"""

    print("\n=== 不同场景配置演示 ===\n")

    scenarios = {
        "开发调试": {
            "monitor": {
                "enabled": True,
                "level": "DEBUG",
                "categories": [
                    "MODEL_INTERACTION",
                    "TOOL_CALLS",
                    "CONTEXT_MANAGEMENT",
                    "ERROR_TRACKING",
                ],
            }
        },
        "生产环境": {
            "monitor": {
                "enabled": True,
                "level": "ERROR",
                "categories": ["ERROR_TRACKING"],
                "handlers": {
                    "console": {"enabled": False},
                    "file": {"enabled": True, "directory": "./prod_logs"},
                },
            }
        },
        "工具开发": {
            "monitor": {
                "enabled": True,
                "level": "DEBUG",
                "categories": ["TOOL_CALLS", "ERROR_TRACKING"],
            }
        },
        "性能分析": {
            "monitor": {
                "enabled": True,
                "level": "INFO",
                "categories": ["PERFORMANCE", "ERROR_TRACKING"],
            }
        },
        "完全禁用": {"monitor": {"enabled": False}},
    }

    from menglong.monitor import load_config_from_dict

    for scenario_name, scenario_config in scenarios.items():
        print(f"{scenario_name}:")
        load_config_from_dict(scenario_config)

        # 测试当前配置
        log_model_interaction(f"{scenario_name}测试", model_id="scenario")
        log_tool_call("scenario_tool", arguments={"scenario": scenario_name})

        status = get_monitor().get_status()
        print(f"  启用分类: {status['enabled_categories']}")
        print(f"  启用级别: {status['enabled_levels']}")
        print()


if __name__ == "__main__":
    print("MengLong 监控配置示例\n")

    # 配置文件演示
    demonstrate_config_file()

    # 环境变量演示
    demonstrate_env_config()

    # 预设配置演示
    demonstrate_preset_configs()

    # 动态配置演示
    demonstrate_dynamic_config()

    # 场景配置演示
    demonstrate_config_scenarios()

    print("\n配置演示完成！")

    # 清理示例文件
    import os

    if os.path.exists("demo_monitor_config.yaml"):
        os.remove("demo_monitor_config.yaml")
        print("已清理示例配置文件")
