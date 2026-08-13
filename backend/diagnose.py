#!/usr/bin/env python3
"""
诊断脚本：检查数据源状态
"""
import sys
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

async def diagnose():
    print("=" * 60)
    print("A股看盘工具 - 数据源诊断")
    print("=" * 60)

    # 1. 检查 AkShare 是否安装
    print("\n1. 检查 AkShare 安装...")
    try:
        import akshare as ak
        print(f"   ✓ AkShare 已安装 (版本: {getattr(ak, '__version__', 'unknown')})")
        akshare_available = True
    except ImportError as e:
        print(f"   ✗ AkShare 未安装: {e}")
        print("   请运行: pip install akshare")
        akshare_available = False

    # 2. 检查网络连接
    if akshare_available:
        print("\n2. 测试 AkShare 数据源...")
        try:
            # 尝试获取一个简单的股票列表
            print("   正在获取股票列表...")
            df = ak.stock_info_a_code_name()
            print(f"   ✓ 成功获取 {len(df)} 只A股")

            # 测试获取实时行情
            print("\n3. 测试获取实时行情...")
            spot_df = ak.stock_zh_a_spot_em()
            print(f"   ✓ 成功获取 {len(spot_df)} 只股票实时行情")

            # 显示几个示例
            print("\n   示例行情:")
            for i, (_, row) in enumerate(spot_df.head(3).iterrows()):
                print(f"     {i+1}. {row['名称']} ({row['代码']}): {row['最新价']}")

            print("\n" + "=" * 60)
            print("✓ 数据源状态正常，应该可以获取真实数据")
            print("=" * 60)

        except Exception as e:
            print(f"   ✗ AkShare 请求失败: {e}")
            print("\n" + "=" * 60)
            print("⚠ 可能原因:")
            print(" 1. 网络连接问题")
            print(" 2. 当前是非交易时间")
            print(" 3. AkShare 数据源临时不可用")
            print("\n 系统将自动使用 Mock 数据作为备选方案")
            print("=" * 60)

if __name__ == "__main__":
    asyncio.run(diagnose())
    input("\n按 Enter 退出...")
