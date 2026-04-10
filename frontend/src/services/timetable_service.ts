// frontend/src/services/timetable.service.ts
import api from './api';

export interface Teacher {
  id: number;
  name: string;
  email: string;
  department: string;
  subjects: string;
}

export interface Subject {
  id: number;
  code: string;
  name: string;
  branch: string;
  year: number;
  teacher_id: number;
  teacher2_id: number | null;
  teacher1_name?: string;
  teacher2_name?: string;
}

export interface Branch {
  code: string;
  name: string;
}

export interface ApiResponse {
  success: boolean;
  message?: string;
}

export interface TimetableData {
  branch: string;
  year: number;
  section: string;
  days: string[];
  time_slots: string[];
  timetable: Record<string, Record<string, string>>;
}

class TimetableService {
  // Teachers (Admin only)
  async addTeacher(data: { name: string; email: string; department: string; subjects: string }): Promise<ApiResponse> {
    return api.post('/admin/teachers', data);
  }

  async getTeachers(): Promise<Teacher[]> {
    const response = await api.get('/teachers');
    return response.data.teachers || [];
  }

  // Subjects (Admin only)
  async addSubject(data: { code: string; name: string; branch: string; year: number; teacher_id: number; teacher2_id?: number }): Promise<ApiResponse> {
    return api.post('/admin/subjects', data);
  }

  async getSubjects(branch: string, year: number): Promise<Subject[]> {
    const response = await api.get(`/subjects/${branch}/${year}`);
    return response.data.subjects || [];
  }

  // Branches
  async getBranches(): Promise<Branch[]> {
    const response = await api.get('/branches');
    return response.data.branches || [];
  }

  // Timetable
  async generateTimetable(branch: string, year: number, section: string): Promise<ApiResponse> {
    return api.post('/timetable/generate', { branch, year, section });
  }

  async viewTimetable(branch: string, year: number, section: string): Promise<TimetableData> {
    const response = await api.get(`/timetable/view/${branch}/${year}/${section}`);
    return response.data;
  }
}

export default new TimetableService();