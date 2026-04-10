// frontend/src/components/Timetable/TimetableGenerator.tsx
import React, { useState, useEffect } from 'react';
import { Calendar, Download, RefreshCw, Filter, Loader2 } from 'lucide-react';
import { timetableService, Course, Room, Slot } from '@/services/timetable.service';
import { useToast } from '@/components/ui/use-toast';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

export const TimetableGenerator: React.FC = () => {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [semester, setSemester] = useState('all');
  const [department, setDepartment] = useState('all');
  const [timetables, setTimetables] = useState<Record<string, any> | null>(null);
  const [activeTab, setActiveTab] = useState<string>('');
  const [courses, setCourses] = useState<Course[]>([]);
  
  // Available semesters (from your C code)
  const semesters = [
    { value: '1', label: 'Semester 1' },
    { value: '3', label: 'Semester 3' },
    { value: '5', label: 'Semester 5' },
    { value: '7', label: 'Semester 7' },
  ];
  
  const departments = [
    { value: 'CSE', label: 'Computer Science' },
    { value: 'ME', label: 'Mechanical Engineering' },
    { value: 'EE', label: 'Electrical Engineering' },
  ];
  
  // Fetch courses on load
  useEffect(() => {
    loadCourses();
  }, []);
  
  const loadCourses = async () => {
    try {
      const data = await timetableService.getCourses();
      setCourses(data);
    } catch (error) {
      console.error('Failed to load courses:', error);
    }
  };
  
  const handleGenerate = async () => {
    setLoading(true);
    try {
      // Filter courses by semester and department
      let filteredCourses = [...courses];
      if (semester !== 'all') {
        filteredCourses = filteredCourses.filter(c => c.semester === semester);
      }
      if (department !== 'all') {
        filteredCourses = filteredCourses.filter(c => c.department === department);
      }
      
      if (filteredCourses.length === 0) {
        toast({
          title: "No courses found",
          description: "Please add courses or change filters",
          variant: "destructive",
        });
        return;
      }
      
      const result = await timetableService.generate(filteredCourses);
      setTimetables(result.timetables);
      
      // Set first tab
      const firstKey = Object.keys(result.timetables)[0];
      if (firstKey) setActiveTab(firstKey);
      
      toast({
        title: "Success!",
        description: result.message,
      });
    } catch (error: any) {
      toast({
        title: "Generation Failed",
        description: error.response?.data?.detail || "Please try again",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };
  
  const handleDownload = async (sem: string, dept: string) => {
    try {
      await timetableService.downloadTimetable(sem, dept, 'txt');
      toast({
        title: "Download Started",
        description: `Downloading timetable for ${dept} Semester ${sem}`,
      });
    } catch (error) {
      toast({
        title: "Download Failed",
        description: "Please try again",
        variant: "destructive",
      });
    }
  };
  
  // Parse semester from filename (csIsem -> 1, CSE)
  const parseFileInfo = (filename: string) => {
    const match = filename.match(/^([a-z]+)([IVX]+)sem\.txt$/i);
    if (!match) return { dept: 'CSE', sem: '1' };
    
    const deptMap: Record<string, string> = {
      cs: 'CSE',
      me: 'ME',
      ee: 'EE',
    };
    
    const semMap: Record<string, string> = {
      I: '1', II: '2', III: '3', IV: '4',
      V: '5', VI: '6', VII: '7', VIII: '8',
    };
    
    return {
      dept: deptMap[match[1].toLowerCase()] || 'CSE',
      sem: semMap[match[2].toUpperCase()] || '1',
    };
  };
  
  const renderTimetable = (data: { headers: string[]; rows: string[][] }) => {
    if (!data.headers.length) {
      return <div className="text-center py-8 text-muted-foreground">No timetable data available</div>;
    }
    
    return (
      <div className="overflow-x-auto">
        <Table className="border">
          <TableHeader>
            <TableRow>
              {data.headers.map((header, idx) => (
                <TableHead key={idx} className="border font-semibold">
                  {header}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.rows.map((row, rowIdx) => (
              <TableRow key={rowIdx}>
                {row.map((cell, cellIdx) => (
                  <TableCell key={cellIdx} className="border">
                    {cell === '.........' ? '—' : cell}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    );
  };
  
  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Timetable Generator</h1>
          <p className="text-muted-foreground">Generate conflict-free timetables using smart scheduling</p>
        </div>
      </div>
      
      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="w-5 h-5" />
            Filters
          </CardTitle>
          <CardDescription>Select semester and department to filter courses</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <div className="w-48">
              <Select value={semester} onValueChange={setSemester}>
                <SelectTrigger>
                  <SelectValue placeholder="Select Semester" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Semesters</SelectItem>
                  {semesters.map(s => (
                    <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="w-48">
              <Select value={department} onValueChange={setDepartment}>
                <SelectTrigger>
                  <SelectValue placeholder="Select Department" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Departments</SelectItem>
                  {departments.map(d => (
                    <SelectItem key={d.value} value={d.value}>{d.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <Button onClick={handleGenerate} disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Calendar className="mr-2 h-4 w-4" />
                  Generate Timetable
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
      
      {/* Results */}
      {timetables && Object.keys(timetables).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Generated Timetables</CardTitle>
            <CardDescription>Click on any timetable to view details</CardDescription>
          </CardHeader>
          <CardContent>
            {/* Tabs */}
            <div className="flex flex-wrap gap-2 mb-6 border-b">
              {Object.entries(timetables).map(([filename, data]) => {
                const { dept, sem } = parseFileInfo(filename);
                return (
                  <button
                    key={filename}
                    onClick={() => setActiveTab(filename)}
                    className={`px-4 py-2 text-sm font-medium transition-colors relative ${
                      activeTab === filename
                        ? 'text-primary border-b-2 border-primary'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    {dept} - Semester {sem}
                  </button>
                );
              })}
            </div>
            
            {/* Active Timetable */}
            {activeTab && timetables[activeTab] && (
              <div className="space-y-4">
                <div className="flex justify-end">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const { dept, sem } = parseFileInfo(activeTab);
                      handleDownload(sem, dept);
                    }}
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Download
                  </Button>
                </div>
                {renderTimetable(timetables[activeTab])}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};