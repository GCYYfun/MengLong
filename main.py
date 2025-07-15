from menglong.utils.log import (
    print_message,
    MessageType,
    configure,
    get_logger,
)


def main():
    # 配置日志
    configure(log_file="menglong.log")
    logger = get_logger()

    logger.info("正在启动 MengLong")
    # print_message(
    #     "Hello from menglong!", MessageType.SUCCESS, title="Welcome", panel=True
    # )
    logger.info("启动完成")


if __name__ == "__main__":
    main()
