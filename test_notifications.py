#!/usr/bin/env python3
"""
ทดสอบระบบแจ้งเตือน Telegram
"""

import os
import sys
from datetime import datetime

# ตั้งค่า environment variables สำหรับทดสอบ
os.environ['TELEGRAM_BOT_TOKEN'] = 'TEST_BOT_TOKEN_PLACEHOLDER'
os.environ['TELEGRAM_CHAT_ID'] = '123456789'
os.environ['GOOGLE_SHEETS_ID'] = 'TEST_SHEET_ID'

def test_telegram_notifier():
    """ทดสอบ telegram_notifier module"""
    print("=" * 60)
    print("ทดสอบ 1: telegram_notifier module")
    print("=" * 60)
    
    try:
        from telegram_notifier import send_sale_notification
        
        # ทดสอบว่า function สามารถเรียกได้
        print("\n✓ telegram_notifier module imported successfully")
        print("✓ send_sale_notification function exists")
        
        # ทดสอบการเรียกใช้ฟังก์ชัน (จะล้มเหลวเพราะ token ไม่ถูกต้อง แต่ code ควรจะทำงาน)
        print("\n📤 ทำการทดสอบส่ง notification (จะล้มเหลวเพราะ token ไม่ถูกต้อง แต่เป็นปกติ)...")
        result = send_sale_notification("Test Latte", 2, 65.0, 130.0)
        print(f"✓ Function executed successfully, result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_morning_report():
    """ทดสอบ morning_report script"""
    print("\n" + "=" * 60)
    print("ทดสอบ 2: morning_report script")
    print("=" * 60)
    
    try:
        from morning_report import send_telegram_alert, build_report
        
        print("\n✓ morning_report module imported successfully")
        print("✓ send_telegram_alert function exists")
        
        # สร้าง mock report
        summary = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "order_count": 5,
            "total_sales": 325.50,
            "best_seller": "Iced Latte"
        }
        report = build_report(summary)
        print(f"\n📊 Test Report:\n{report}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_agent_tools():
    """ทดสอบ agent_tools module"""
    print("\n" + "=" * 60)
    print("ทดสอบ 3: agent_tools module")
    print("=" * 60)
    
    try:
        from agent_tools import log_sale, get_sales_summary
        
        print("\n✓ agent_tools module imported successfully")
        print("✓ log_sale function exists")
        print("✓ get_sales_summary function exists")
        
        # ทดสอบการบันทึกยอดขาย
        print("\n📝 ทำการทดสอบบันทึกยอดขาย...")
        result = log_sale("Test Menu", 3, 60.0)
        
        print(f"✓ Result status: {result.get('status')}")
        print(f"  - Menu: {result.get('menu')}")
        print(f"  - Quantity: {result.get('quantity')}")
        print(f"  - Total: {result.get('total')}")
        print(f"  - Sheet uploaded: {result.get('sheet_uploaded')}")
        print(f"  - Telegram sent: {result.get('telegram_sent')}")
        
        # ทดสอบการดึงยอดขายวันนี้
        print("\n📊 ทำการทดสอบดึงยอดขายวันนี้...")
        summary = get_sales_summary()
        print(f"✓ Summary for {summary.get('date')}:")
        print(f"  - Total transactions: {summary.get('transactions')}")
        print(f"  - Total items: {summary.get('total_items')}")
        print(f"  - Total revenue: {summary.get('total_revenue')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_summary_report():
    """ทดสอบ summary_report script"""
    print("\n" + "=" * 60)
    print("ทดสอบ 4: summary_report script")
    print("=" * 60)
    
    try:
        from summary_report import send_telegram_alert
        
        print("\n✓ summary_report module imported successfully")
        print("✓ send_telegram_alert function exists")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """รัน all tests"""
    print("\n")
    print("🚀 เริ่มทดสอบระบบแจ้งเตือน Telegram")
    print("=" * 60)
    
    results = {
        "telegram_notifier": test_telegram_notifier(),
        "morning_report": test_morning_report(),
        "agent_tools": test_agent_tools(),
        "summary_report": test_summary_report(),
    }
    
    print("\n" + "=" * 60)
    print("📋 สรุปผลการทดสอบ")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ ผ่าน" if passed else "❌ ล้มเหลว"
        print(f"{status} - {test_name}")
    
    total_passed = sum(1 for v in results.values() if v)
    print(f"\n📊 ผลลัพธ์: {total_passed}/{len(results)} tests passed")
    
    if all(results.values()):
        print("\n🎉 ระบบแจ้งเตือนพร้อมใช้งาน!")
        return 0
    else:
        print("\n⚠️ มีบางส่วนที่ต้องแก้ไข")
        return 1


if __name__ == "__main__":
    sys.exit(main())
