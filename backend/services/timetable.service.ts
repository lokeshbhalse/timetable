// frontend/src/services/timetable.service.ts
import api from './api';

export interface Course {
  course_name: string;
  no_of_students: number;
  semester: string;
  department: string;
  lab: 'y' | 'n';
  preference: number;
  preferred_room?: string;
  preferred_slot?: string;
  division?: string;
}

export interface Room {
  room_no: string;
  capacity: number;
}

export interface Slot {
  slot_id: number;
  slot_name: string;
  day: string;
  time_from: string;
  till_time: string;
}

export interface TimetableResponse {
  status: string;
  timetables: Record<string, { headers: string[]; rows: string[][] }>;
  message: string;
}

export const timetableService = {
  // Generate timetable
  generate: async (courses: Course[]): Promise<TimetableResponse> => {
    const response = await api.post('/timetable/generate', { courses });
    return response.data;
  },
  
  // Get specific timetable
  getTimetable: async (semester: string, department: string) => {
    const response = await api.get(`/timetable/${semester}/${department}`);
    return response.data;
  },
  
  // Download timetable
  downloadTimetable: async (semester: string, department: string, format: string = 'txt') => {
    const response = await api.get(`/timetable/download/${semester}/${department}/${format}`, {
      responseType: 'blob'
    });
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `timetable_${semester}_${department}.${format}`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
  
  // Courses
  getCourses: async (semester?: string, department?: string) => {
    let url = '/courses';
    const params = new URLSearchParams();
    if (semester) params.append('semester', semester);
    if (department) params.append('department', department);
    if (params.toString()) url += `?${params.toString()}`;
    
    const response = await api.get(url);
    return response.data;
  },
  
  createCourse: async (course: Course) => {
    const response = await api.post('/courses', course);
    return response.data;
  },
  
  updateCourse: async (courseName: string, course: Course) => {
    const response = await api.put(`/courses/${encodeURIComponent(courseName)}`, course);
    return response.data;
  },
  
  deleteCourse: async (courseName: string) => {
    const response = await api.delete(`/courses/${encodeURIComponent(courseName)}`);
    return response.data;
  },
  
  // Rooms
  getRooms: async () => {
    const response = await api.get('/rooms');
    return response.data;
  },
  
  createRoom: async (room: Room) => {
    const response = await api.post('/rooms', room);
    return response.data;
  },
  
  deleteRoom: async (roomNo: string) => {
    const response = await api.delete(`/rooms/${encodeURIComponent(roomNo)}`);
    return response.data;
  },
  
  // Slots
  getSlots: async () => {
    const response = await api.get('/slots');
    return response.data;
  },
  
  createSlot: async (slot: Slot) => {
    const response = await api.post('/slots', slot);
    return response.data;
  },
  
  deleteSlot: async (slotId: number) => {
    const response = await api.delete(`/slots/${slotId}`);
    return response.data;
  },
  
  // Faculty
  getFaculty: async () => {
    const response = await api.get('/faculty');
    return response.data;
  },
  
  createFaculty: async (faculty: any) => {
    const response = await api.post('/faculty', faculty);
    return response.data;
  },
  
  // Health check
  healthCheck: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};