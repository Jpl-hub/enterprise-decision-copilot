from __future__ import annotations


def main() -> None:
    raise SystemExit(
        "scripts/build_real_processed_data.py 已停用。该旧脚本曾服务于早期演示数据，不再允许作为正式数据入口。"
        "请改用官方来源流水线：scripts/refresh_real_data_pipeline.py、scripts/fetch_*_official_reports.py、"
        "scripts/fetch_eastmoney_*_reports.py 和 scripts/fetch_official_macro_indicators.py。"
    )


if __name__ == '__main__':
    main()
