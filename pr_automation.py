"""
GitHub PR Automation Module

อ่าน trace log แล้วสร้าง Pull Request อัตโนมัติ
- อ่าน agent_trace.log
- สร้าง PR description จาก trace data
- เปิด Pull Request ไปยัง GitHub
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any

from dotenv import load_dotenv
from github import Github

load_dotenv()


class PRAutomation:
    """จัดการการสร้าง Pull Request อัตโนมัติ"""
    
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise RuntimeError("ไม่พบ GITHUB_TOKEN ในไฟล์ .env")
        
        self.github = Github(self.github_token)
        self.trace_file = "agent_trace.log"
        
        # ดึงข้อมูล repo จาก environment
        self.repo_name = os.getenv("GITHUB_REPOSITORY", "Nattawut539/MilkyMood-AI")
        self.repo = self.github.get_repo(self.repo_name)
    
    def read_trace_log(self) -> List[Dict[str, Any]]:
        """อ่าน trace log และแปลงเป็น list ของ events"""
        if not os.path.exists(self.trace_file):
            return []
        
        events = []
        with open(self.trace_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    events.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
        return events
    
    def analyze_trace(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """วิเคราะห์ trace events และสรุปเป็น PR description"""
        
        # Filter events จาก session ล่าสุด (วันนี้)
        today = datetime.now().strftime("%Y-%m-%d")
        today_events = [
            e for e in events 
            if e.get("timestamp", "").startswith(today)
        ]
        
        # สรุป actions ที่ทำ
        actions_summary = {}
        user_inputs = []
        tool_results = []
        
        for event in today_events:
            event_type = event.get("event")
            
            if event_type == "user_input":
                user_inputs.append(event.get("message", ""))
            
            elif event_type == "tool_result":
                action = event.get("action")
                result = event.get("result", {})
                
                if action not in actions_summary:
                    actions_summary[action] = []
                actions_summary[action].append(result)
                
                tool_results.append({
                    "action": action,
                    "result": result
                })
        
        # สร้าง PR description
        pr_description = self._generate_pr_description(
            user_inputs, actions_summary, tool_results
        )
        
        return {
            "date": today,
            "total_events": len(today_events),
            "user_inputs": user_inputs,
            "actions_summary": actions_summary,
            "tool_results": tool_results,
            "pr_description": pr_description
        }
    
    def _generate_pr_description(
        self, 
        user_inputs: List[str], 
        actions_summary: Dict[str, List], 
        tool_results: List[Dict]
    ) -> str:
        """สร้าง PR description จากข้อมูล trace"""
        
        lines = []
        lines.append("## 🤖 Agent Harness Session Report")
        lines.append("")
        lines.append(f"**วันที่:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**จำนวนคำสั่ง:** {len(user_inputs)}")
        lines.append("")
        
        # สรุป actions
        if actions_summary:
            lines.append("## 📊 Actions Performed")
            lines.append("")
            
            for action, results in actions_summary.items():
                lines.append(f"### {action.replace('_', ' ').title()}")
                lines.append(f"- **จำนวนครั้ง:** {len(results)}")
                
                if action == "log_sale":
                    total_sales = sum(r.get("total", 0) for r in results)
                    lines.append(f"- **ยอดขายรวม:** {total_sales} บาท")
                    
                elif action == "order":
                    total_orders = sum(r.get("total", 0) for r in results)
                    lines.append(f"- **คำสั่งซื้อรวม:** {total_orders} บาท")
                    
                elif action == "get_summary":
                    lines.append("- **ดึงสรุปรายงาน**")
                    
                elif action == "send_notification":
                    lines.append("- **ส่งแจ้งเตือน**")
                
                lines.append("")
        
        # รายละเอียดคำสั่ง
        if user_inputs:
            lines.append("## 💬 User Commands")
            lines.append("")
            for i, cmd in enumerate(user_inputs, 1):
                lines.append(f"{i}. `{cmd}`")
            lines.append("")
        
        # Trace data (JSON)
        lines.append("## 🔍 Trace Data")
        lines.append("")
        lines.append("```json")
        trace_data = {
            "session_date": datetime.now().isoformat(),
            "user_commands": user_inputs,
            "actions_summary": actions_summary,
            "tool_results": tool_results
        }
        lines.append(json.dumps(trace_data, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")
        
        lines.append("---")
        lines.append("*Generated by Agent Harness*")
        
        return "\n".join(lines)
    
    def create_pull_request(
        self, 
        title: str = None, 
        head_branch: str = None,
        base_branch: str = "main"
    ) -> Dict[str, Any]:
        """สร้าง Pull Request"""
        
        # อ่านและวิเคราะห์ trace
        events = self.read_trace_log()
        analysis = self.analyze_trace(events)
        
        # สร้าง title ถ้าไม่ได้ระบุ
        if not title:
            action_count = len(analysis.get("actions_summary", {}))
            title = f"🤖 Agent Session: {action_count} actions performed"
        
        # สร้าง head branch ถ้าไม่ได้ระบุ
        if not head_branch:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            head_branch = f"agent-session-{timestamp}"
        
        # สร้าง PR
        try:
            pr = self.repo.create_pull(
                title=title,
                body=analysis["pr_description"],
                head=head_branch,
                base=base_branch
            )
            
            return {
                "status": "success",
                "pr_number": pr.number,
                "pr_url": pr.html_url,
                "title": pr.title,
                "analysis": analysis
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "analysis": analysis
            }
    
    def get_recent_sessions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """ดึงข้อมูล sessions ล่าสุด"""
        events = self.read_trace_log()
        
        # Group by date
        sessions = {}
        for event in events:
            date = event.get("timestamp", "")[:10]  # YYYY-MM-DD
            if date not in sessions:
                sessions[date] = []
            sessions[date].append(event)
        
        # Return recent sessions
        recent_dates = sorted(sessions.keys(), reverse=True)[:limit]
        return [
            {
                "date": date,
                "events": sessions[date],
                "event_count": len(sessions[date])
            }
            for date in recent_dates
        ]


def create_pr_from_trace(
    title: str = None,
    head_branch: str = None,
    base_branch: str = "main"
) -> Dict[str, Any]:
    """ฟังก์ชันหลักสำหรับสร้าง PR จาก trace"""
    try:
        pr_auto = PRAutomation()
        return pr_auto.create_pull_request(title, head_branch, base_branch)
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


if __name__ == "__main__":
    # ทดสอบ PR automation
    print("🔄 Analyzing trace log...")
    
    pr_auto = PRAutomation()
    
    # อ่าน trace
    events = pr_auto.read_trace_log()
    print(f"📊 Found {len(events)} events in trace log")
    
    # วิเคราะห์
    analysis = pr_auto.analyze_trace(events)
    print(f"📅 Session date: {analysis['date']}")
    print(f"💬 User commands: {len(analysis['user_inputs'])}")
    print(f"⚙️ Actions performed: {list(analysis['actions_summary'].keys())}")
    
    # แสดง PR description preview
    print("\n📝 PR Description Preview:")
    print("=" * 50)
    print(analysis['pr_description'][:500] + "..." if len(analysis['pr_description']) > 500 else analysis['pr_description'])
    print("=" * 50)
    
    # ถามก่อนสร้าง PR จริง
    create_real_pr = input("\n❓ Create real Pull Request? (y/N): ").lower().strip()
    if create_real_pr == 'y':
        print("🚀 Creating Pull Request...")
        result = pr_auto.create_pull_request()
        
        if result["status"] == "success":
            print("✅ PR Created Successfully!")
            print(f"🔗 URL: {result['pr_url']}")
            print(f"📋 Number: #{result['pr_number']}")
        else:
            print(f"❌ Failed to create PR: {result['error']}")
    else:
        print("⏭️ Skipped PR creation")</content>
<parameter name="filePath">/workspaces/MilkyMood-AI/pr_automation.py