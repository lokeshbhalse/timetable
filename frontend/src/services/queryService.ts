// frontend/src/services/queryService.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from './api';

// Query keys for caching
export const queryKeys = {
  teachers: 'teachers',
  subjects: 'subjects',
  users: 'users',
  timetable: 'timetable',
  sections: 'sections',
};

// Fetch functions
const fetchTeachers = async () => {
  const response = await api.get('/admin/teachers');
  return response.data.teachers;
};

const fetchSubjects = async (branch: string, year: number) => {
  const response = await api.get('/admin/subjects', {
    params: { branch, year }
  });
  return response.data.subjects;
};

const fetchUsers = async () => {
  const response = await api.get('/admin/users');
  return response.data.users;
};

const fetchTimetable = async (branch: string, year: number, section: string) => {
  const response = await api.get('/timetable/view', {
    params: { branch, year, section }
  });
  return response.data.timetable;
};

// Hooks for real-time data
export const useTeachers = () => {
  return useQuery({
    queryKey: [queryKeys.teachers],
    queryFn: fetchTeachers,
    refetchInterval: 5000, // Auto-refresh every 5 seconds
  });
};

export const useSubjects = (branch: string, year: number) => {
  return useQuery({
    queryKey: [queryKeys.subjects, branch, year],
    queryFn: () => fetchSubjects(branch, year),
    enabled: !!branch && !!year,
    refetchInterval: 5000,
  });
};

export const useUsers = () => {
  return useQuery({
    queryKey: [queryKeys.users],
    queryFn: fetchUsers,
    refetchInterval: 3000, // Refresh every 3 seconds
  });
};

export const useTimetable = (branch: string, year: number, section: string) => {
  return useQuery({
    queryKey: [queryKeys.timetable, branch, year, section],
    queryFn: () => fetchTimetable(branch, year, section),
    enabled: !!branch && !!year && !!section,
    refetchInterval: 10000, // Refresh every 10 seconds
  });
};

// Mutations for real-time updates
export const useAddTeacher = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (teacherData: { name: string; email: string; department: string; subjects: string }) => api.post('/admin/teachers', teacherData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [queryKeys.teachers] });
    },
  });
};

export const useAddSubject = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (subjectData: { code: string; name: string; branch: string; year: number; teacher_id: number }) => api.post('/admin/subjects', subjectData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [queryKeys.subjects] });
    },
  });
};

export const useGenerateTimetable = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { branch: string; year: number; section: string; semester: number }) => api.post('/timetable/generate', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [queryKeys.timetable] });
    },
  });
};