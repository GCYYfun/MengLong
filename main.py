from menglong.utils.log.logging_tool import (
    print,
    MessageType,
    configure_logger,
    get_logger,
)


def main():
    # 配置日志
    configure_logger(log_file="menglong.log")
    logger = get_logger()

    logger.info("正在启动 MengLong")
    print("Hello from menglong!", MessageType.SUCCESS, title="Welcome", use_panel=True)
    logger.debug("启动完成")


if __name__ == "__main__":
    main()
