# backend/services/scheduler.py
import subprocess
import os
import sys
from typing import Dict, List, Any
from backend.config import config

class TimetableScheduler:
    """Wrapper for your existing C scheduling algorithm"""
    
    def __init__(self):
        self.base_dir = config.BASE_DIR
        self.data_dir = os.path.join(self.base_dir, "data")
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
    
    def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate timetable using your C program (new.c / tt.exe)"""
        
        # Prepare course file if courses provided
        if params.get('courses'):
            self._create_course_file(params['courses'])
        
        # Run the C program
        result = self._run_c_scheduler()
        
        if not result:
            # Fall back to Python
            result = self._run_python_scheduler()
        
        if not result:
            return {"error": "Failed to generate timetable", "timetables": {}}
        
        # Parse output files
        timetables = self._parse_timetable_files()
        
        return timetables
    
    def _run_c_scheduler(self) -> bool:
        """Run the C executable (compiled from new.c)"""
        try:
            # Look for tt.exe in various locations
            exe_paths = [
                os.path.join(self.base_dir, "tt.exe"),
                os.path.join(self.base_dir, "tt"),
                os.path.join(self.base_dir, "new.exe"),
                os.path.join(self.base_dir, "a.out"),
            ]
            
            exe_path = None
            for path in exe_paths:
                if os.path.exists(path):
                    exe_path = path
                    break
            
            if not exe_path:
                print("C executable not found")
                return False
            
            # Run the executable
            result = subprocess.run(
                [exe_path],
                capture_output=True,
                text=True,
                cwd=self.base_dir,  # Run from base dir so it finds txt files
                timeout=60
            )
            
            print(f"C program output: {result.stdout}")
            if result.stderr:
                print(f"C program errors: {result.stderr}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("C scheduler timed out")
            return False
        except Exception as e:
            print(f"C scheduler error: {e}")
            return False
    
    def _run_python_scheduler(self) -> bool:
        """Run Python scheduler as fallback"""
        try:
            # Add legacy directory to path
            sys.path.insert(0, os.path.join(self.base_dir, "backend", "legacy"))
            
            # Import and run
            from Main import generate_timetable_from_files
            return generate_timetable_from_files()
            
        except Exception as e:
            print(f"Python scheduler error: {e}")
            return False
    
    def _create_course_file(self, courses: List[Dict]) -> None:
        """Create course_file.txt from course data (matching new.c format)"""
        filepath = os.path.join(self.base_dir, "course_file.txt")
        
        with open(filepath, "w") as f:
            f.write(f"{len(courses)}\n")
            for course in courses:
                # Format: course_name no_of_students color1 color2 color3 lab
                colors = self._get_semester_colors(course['semester'], course['department'])
                f.write(f"{course['course_name']} {course['no_of_students']} ")
                for color in colors:
                    f.write(f"{color} ")
                f.write(f"{course.get('lab', 'n')}\n")
        
        print(f"Created course_file.txt with {len(courses)} courses")
    
    def _get_semester_colors(self, semester: str, department: str) -> List[int]:
        """Map semester to color codes (from new.c's color array)"""
        color_map = {
            ("1", "CSE"): [1, 0, 0],
            ("3", "CSE"): [0, 2, 0],
            ("3", "ME"): [0, 0, 3],
            ("3", "EE"): [0, 0, 0, 4],
            ("5", "CSE"): [0, 0, 0, 0, 5],
            ("5", "ME"): [0, 0, 0, 0, 0, 6],
            ("5", "EE"): [0, 0, 0, 0, 0, 0, 7],
            ("7", "CSE"): [0, 0, 0, 0, 0, 0, 0, 8],
            ("7", "ME"): [0, 0, 0, 0, 0, 0, 0, 0, 9],
            ("7", "EE"): [0, 0, 0, 0, 0, 0, 0, 0, 0, 10],
        }
        return color_map.get((semester, department), [1, 0, 0])
    
    def _parse_timetable_files(self) -> Dict[str, Any]:
        """Parse all generated timetable files"""
        semesters = ["csIsem", "csIIIsem", "meIIIsem", "eeIIIsem", 
                     "csVsem", "meVsem", "eeVsem", "csVIIsem", "meVIIsem", "eeVIIsem"]
        
        timetables = {}
        for sem in semesters:
            filepath = os.path.join(self.base_dir, f"{sem}.txt")
            if os.path.exists(filepath):
                with open(filepath, "r", encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    timetables[sem] = self._parse_timetable_content(content)
        
        return timetables
    
    def _parse_timetable_content(self, content: str) -> Dict:
        """Parse timetable text content (tab-separated format from new.c)"""
        lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
        
        if not lines:
            return {"headers": [], "rows": []}
        
        # First line contains headers (Day, 8:30-9:25, etc.)
        headers = lines[0].split('\t')
        
        # Parse each row
        rows = []
        for line in lines[1:]:
            if line.strip():
                row = line.split('\t')
                rows.append(row)
        
        return {
            "headers": headers,
            "rows": rows
        }