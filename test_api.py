#!/usr/bin/env python3
"""
Simple curl-based test for the timetable API
Run this after: python main.py
"""

import subprocess
import json
import sys
import time

def run_test():
    """Test the timetable API with 20 sections"""
    
    print("=" * 70)
    print("  🚀 TIMETABLE GENERATOR API TEST - 20 Sections")
    print("=" * 70)
    print()
    
    # Define the payload
    payload = {
        "start_time": "08:00",
        "end_time": "18:00",
        "duration": 50,
        "sections": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", 
                     "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T"],
        "subjects": [
            {"name": "Mathematics", "is_lab": False, "credits": 4},
            {"name": "Physics", "is_lab": False, "credits": 3},
            {"name": "Chemistry", "is_lab": False, "credits": 3},
            {"name": "English", "is_lab": False, "credits": 2},
            {"name": "Data Science", "is_lab": False, "credits": 3},
            {"name": "OOP", "is_lab": False, "credits": 3},
            {"name": "Physics Lab", "is_lab": True, "credits": 2},
            {"name": "Chemistry Lab", "is_lab": True, "credits": 2},
            {"name": "DS Lab", "is_lab": True, "credits": 1}
        ],
        "rooms": [
            {"block": "THEORY", "start": 101, "end": 116},
            {"block": "LAB", "start": 1, "end": 48}
        ],
        "faculty": [
            {"name": "Dr. Smith", "subjects": ["Mathematics"]},
            {"name": "Dr. Johnson", "subjects": ["Physics"]},
            {"name": "Dr. Williams", "subjects": ["Chemistry"]},
            {"name": "Prof. Brown", "subjects": ["English"]},
            {"name": "Prof. Davis", "subjects": ["Data Science"]},
            {"name": "Prof. Miller", "subjects": ["OOP"]},
            {"name": "Lab Tech A", "subjects": ["Physics Lab"]},
            {"name": "Lab Tech B", "subjects": ["Chemistry Lab"]},
            {"name": "Lab Tech C", "subjects": ["DS Lab"]}
        ]
    }
    
    # Configuration
    config = {
        "sections": 20,
        "theory_rooms": round(0.8 * 20),
        "lab_rooms": round(0.8 * 20 * 3),
        "faculty_count": len(payload["faculty"]),
        "subjects_count": len(payload["subjects"])
    }
    
    print("📋 Configuration:")
    print(f"   • Sections: {config['sections']}")
    print(f"   • Theory Rooms: {config['theory_rooms']} (0.8× budget)")
    print(f"   • Lab Rooms: {config['lab_rooms']} (0.8× budget, 3 subgroups)")
    print(f"   • Faculty: {config['faculty_count']}")
    print(f"   • Subjects: {config['subjects_count']}")
    print()
    
    # Save payload to JSON file
    print("💾 Saving payload to 'payload_test.json'...")
    with open('payload_test.json', 'w') as f:
        json.dump(payload, f, indent=2)
    print()
    
    # Run curl command
    print("🌐 Sending request to http://127.0.0.1:8000/api/generate/")
    print()
    
    url = "http://127.0.0.1:8000/api/generate/"
    
    try:
        # Use subprocess to run curl
        cmd = [
            "curl", "-X", "POST", url,
            "-H", "Content-Type: application/json",
            "-d", json.dumps(payload)
        ]
        
        print("   ⏳ Processing... (this may take 1-5 minutes)")
        start = time.time()
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        elapsed = time.time() - start
        
        if result.returncode != 0:
            print(f"\n   ❌ Error: {result.stderr}")
            return False
        
        response = json.loads(result.stdout)
        
        print(f"   ✅ Success! (Took {elapsed:.1f}s)")
        print()
        print("📊 Results:")
        print(f"   • Total Classes: {len(response.get('schedule', []))}")
        print(f"   • Time Slots: {len(response.get('time_slots', []))}")
        print()
        
        if response.get('schedule'):
            print("   First 5 classes:")
            for cls in response['schedule'][:5]:
                print(f"     - {cls['section']} | {cls['subject']:<15} | "
                      f"{cls['day'][:3]} {cls['start_time']}-{cls['end_time']} | "
                      f"{cls['teacher']:<15} | {cls['room']}")
        
        print()
        print("🎉 SUCCESS! Full response saved to 'response.json'")
        with open('response.json', 'w') as f:
            json.dump(response, f, indent=2)
        
        print()
        print("📱 Next Steps:")
        print("   1. Open http://localhost:8080 in your browser")
        print("   2. Navigate to Dashboard → Latest Schedule")
        print("   3. View the complete timetable with drag-and-drop interface")
        
        return True
        
    except subprocess.TimeoutExpired:
        print("\n   ⏱️ Request timed out (>10 minutes)")
        return False
    except json.JSONDecodeError:
        print("\n   ❌ Failed to parse response as JSON")
        print(f"   Response: {result.stdout[:200]}")
        return False
    except Exception as e:
        print(f"\n   ❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
