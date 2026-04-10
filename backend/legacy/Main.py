# backend/legacy/Main.py

from Bipartite_Matching_Assignment import *
import sys
import os

def TestMaximumBipartiteMatching():
    V1, V2, E = [], [], []
    
    try:
        m = int(input())
        for i in range(m):
            v1, v2 = input().split()
            V1.append(v1)
            V2.append(v2)
            E.append((v1, v2))

        B = BipartiteGraph(V1, V2, E)
        result = MaximumCardinalityMatching(B, [])
        print("Maximum Matching:", result)
        return result
    except Exception as e:
        print(f"Error in TestMaximumBipartiteMatching: {e}")
        return []

def TestAssignmentProblem():
    try:
        V1, V2, E, W = [], [], [], []
        
        # Try to open input_graph.txt
        input_path = "input_graph.txt"
        if not os.path.exists(input_path):
            print(f"Warning: {input_path} not found, creating sample data")
            return []
            
        with open(input_path, "r") as input_graph:
            m = int(input_graph.readline())
            for i in range(m):
                line = input_graph.readline()
                if not line:
                    break
                parts = line.split()
                if len(parts) >= 3:
                    v1, v2, w = parts[0], parts[1], parts[2]
                    V1.append(v1)
                    V2.append(v2)
                    E.append((v1, v2))
                    W.append(float(w))

        if not V1 or not V2:
            print("No data to process")
            return []

        B = BipartiteGraph(V1, V2, E, W)
        temp = AssignmentProblem(B)
        
        with open('output_graph.txt', 'w') as fp:
            for x in temp:
                fp.write(f"{x[0]} {x[1]}\n")
        
        print(f"Assignment Problem completed. Output written to output_graph.txt")
        return temp
        
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        return []
    except Exception as e:
        print(f"Error in TestAssignmentProblem: {e}")
        return []

def generate_timetable_from_files():
    """Main function to generate timetable from existing data files"""
    print("=" * 60)
    print("Timetable Generator - Running Scheduling Algorithm")
    print("=" * 60)
    
    # Check if required files exist
    required_files = ["course_file.txt", "room_file.txt", "slot_file.txt"]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"Error: Missing required files: {missing_files}")
        print("Please ensure course_file.txt, room_file.txt, and slot_file.txt exist")
        return False
    
    try:
        # Run the assignment problem
        result = TestAssignmentProblem()
        
        if result:
            print("\n✓ Timetable generated successfully!")
            print("Generated files:")
            for sem_file in ["csIsem.txt", "csIIIsem.txt", "meIIIsem.txt", "eeIIIsem.txt",
                            "csVsem.txt", "meVsem.txt", "eeVsem.txt", 
                            "csVIIsem.txt", "meVIIsem.txt", "eeVIIsem.txt"]:
                if os.path.exists(sem_file):
                    print(f"  - {sem_file}")
            return True
        else:
            print("Failed to generate timetable")
            return False
            
    except Exception as e:
        print(f"Error during timetable generation: {e}")
        return False

if __name__ == '__main__':
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description='Timetable Generator')
    parser.add_argument('--mode', choices=['matching', 'assignment', 'full'], 
                       default='full', help='Mode to run')
    parser.add_argument('--quiet', action='store_true', help='Suppress output')
    
    args = parser.parse_args()
    
    if args.mode == 'matching':
        TestMaximumBipartiteMatching()
    elif args.mode == 'assignment':
        TestAssignmentProblem()
    else:
        generate_timetable_from_files()