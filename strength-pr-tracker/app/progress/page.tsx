'use client';

import { DashboardLayout } from '@/components/DashboardLayout';
import { TrendingUp, Calendar, Target, Activity, BarChart3 } from 'lucide-react';
import Link from 'next/link';
import { useState, useEffect } from 'react';

interface Exercise {
  _id: string;
  name: string;
}

interface Set {
  weight: number;
  reps: number;
  rpe?: number;
  notes?: string;
}

interface PersonalRecord {
  _id: string;
  exerciseId: Exercise;
  date: string;
  sets: Set[];
  sessionNotes?: string;
  totalVolume: number;
  maxWeight: number;
  maxReps: number;
  isPersonalBest: boolean;
  pbType: string;
  createdAt: string;
}

export default function ProgressPage() {
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [sessions, setSessions] = useState<PersonalRecord[]>([]);
  const [selectedExercise, setSelectedExercise] = useState<string>('all');
  const [timeRange, setTimeRange] = useState<string>('30');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        const [exercisesRes, sessionsRes] = await Promise.all([
          fetch('/api/exercise'),
          fetch('/api/personal-record')
        ]);
        
        const exercisesData = await exercisesRes.json();
        const sessionsData = await sessionsRes.json();
        
        setExercises(exercisesData);
        setSessions(sessionsData);
      } catch (error) {
        console.error('Error fetching progress data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const getFilteredSessions = () => {
    let filtered = sessions;
    
    // Filter by exercise
    if (selectedExercise !== 'all') {
      filtered = filtered.filter(s => s.exerciseId._id === selectedExercise);
    }
    
    // Filter by time range
    const now = new Date();
    const daysAgo = new Date(now.getTime() - (parseInt(timeRange) * 24 * 60 * 60 * 1000));
    filtered = filtered.filter(s => new Date(s.date) >= daysAgo);
    
    return filtered.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  };

  const getProgressData = () => {
    const filteredSessions = getFilteredSessions();
    
    return filteredSessions.map(session => ({
      date: new Date(session.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      weight: session.maxWeight,
      reps: session.maxReps,
      volume: session.totalVolume,
      sets: session.sets.length
    }));
  };

  const getProgressSummary = () => {
    const filteredSessions = getFilteredSessions();
    if (filteredSessions.length === 0) return null;
    
    const firstSession = filteredSessions[0];
    const lastSession = filteredSessions[filteredSessions.length - 1];
    
    const weightProgress = lastSession.maxWeight - firstSession.maxWeight;
    const repsProgress = lastSession.maxReps - firstSession.maxReps;
    const volumeProgress = lastSession.totalVolume - firstSession.totalVolume;
    
    return {
      weightProgress,
      repsProgress,
      volumeProgress,
      sessionsCount: filteredSessions.length,
      totalVolume: filteredSessions.reduce((total, s) => total + s.totalVolume, 0)
    };
  };

  const getTopPerformances = () => {
    const filteredSessions = getFilteredSessions();
    if (filteredSessions.length === 0) return [];
    
    // Get the best performance for each exercise
    const exerciseBest = new Map<string, PersonalRecord>();
    
    filteredSessions.forEach(session => {
      const exerciseId = session.exerciseId._id;
      const existing = exerciseBest.get(exerciseId);
      
      if (!existing || session.totalVolume > existing.totalVolume) {
        exerciseBest.set(exerciseId, session);
      }
    });
    
    return Array.from(exerciseBest.values())
      .sort((a, b) => b.totalVolume - a.totalVolume)
      .slice(0, 5);
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading progress data...</p>
        </div>
      </DashboardLayout>
    );
  }

  const progressData = getProgressData();
  const progressSummary = getProgressSummary();
  const topPerformances = getTopPerformances();

  return (
    <DashboardLayout>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Training Progress</h1>
        <p className="text-gray-600">
          Track your strength gains and training improvements over time
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm mb-8">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <label htmlFor="exercise" className="block text-sm font-medium text-gray-700 mb-2">
              Exercise Type
            </label>
            <select
              id="exercise"
              value={selectedExercise}
              onChange={(e) => setSelectedExercise(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Exercises</option>
              {exercises.map((exercise) => (
                <option key={exercise._id} value={exercise._id}>
                  {exercise.name}
                </option>
              ))}
            </select>
          </div>
          
          <div className="flex-1">
            <label htmlFor="timeRange" className="block text-sm font-medium text-gray-700 mb-2">
              Time Range
            </label>
            <select
              id="timeRange"
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
              <option value="90">Last 3 months</option>
              <option value="180">Last 6 months</option>
              <option value="365">Last year</option>
            </select>
          </div>
        </div>
      </div>

      {/* Progress Summary */}
      {progressSummary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Activity className="h-5 w-5 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Sessions</p>
                <p className="text-2xl font-bold text-gray-900">{progressSummary.sessionsCount}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <TrendingUp className="h-5 w-5 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Weight Progress</p>
                <p className={`text-2xl font-bold ${progressSummary.weightProgress >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {progressSummary.weightProgress >= 0 ? '+' : ''}{progressSummary.weightProgress} kg
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Target className="h-5 w-5 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Reps Progress</p>
                <p className={`text-2xl font-bold ${progressSummary.repsProgress >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {progressSummary.repsProgress >= 0 ? '+' : ''}{progressSummary.repsProgress}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <div className="flex items-center">
              <div className="p-2 bg-orange-100 rounded-lg">
                <BarChart3 className="h-5 w-5 text-orange-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Volume Progress</p>
                <p className={`text-2xl font-bold ${progressSummary.volumeProgress >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {progressSummary.volumeProgress >= 0 ? '+' : ''}{progressSummary.volumeProgress} kg
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Progress Chart */}
      {progressData.length > 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm mb-8">
          <h3 className="text-lg font-medium text-gray-900 mb-6">Progress Over Time</h3>
          <div className="h-64 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center">
            <div className="text-center text-gray-500">
              <BarChart3 className="h-12 w-12 mx-auto mb-2" />
              <p className="text-sm">Progress chart will appear here</p>
              <p className="text-xs">Chart visualization coming soon</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm mb-8">
          <div className="text-center py-12">
            <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No progress data</h3>
            <p className="text-gray-600 mb-6">
              {selectedExercise === 'all' 
                ? 'No training sessions found for the selected time range'
                : 'No sessions found for this exercise in the selected time range'
              }
            </p>
            <Link
              href="/personal-record/new"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Activity className="h-4 w-4 mr-2" />
              Log Training Session
            </Link>
          </div>
        </div>
      )}

      {/* Top Performances */}
      {topPerformances.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm mb-8">
          <h3 className="text-lg font-medium text-gray-900 mb-6">Top Performances</h3>
          <div className="space-y-4">
            {topPerformances.map((session, index) => (
              <div key={session._id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-bold">
                    {index + 1}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{session.exerciseId.name}</p>
                    <p className="text-sm text-gray-600">
                      {new Date(session.date).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                
                <div className="text-right">
                  <p className="font-medium text-gray-900">{session.totalVolume.toLocaleString()} kg</p>
                  <p className="text-sm text-gray-600">
                    {session.maxWeight} kg × {session.maxReps} reps
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Progress Insights */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl border border-blue-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">💡 Progress Insights</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-700">
          <div>
            <p className="font-medium mb-2">Consistent Training</p>
            <p>Regular sessions are key to progress. Aim for consistent frequency rather than sporadic intense workouts.</p>
          </div>
          <div>
            <p className="font-medium mb-2">Progressive Overload</p>
            <p>Gradually increase weight, reps, or volume over time to continue making strength gains.</p>
          </div>
          <div>
            <p className="font-medium mb-2">Plateau Recognition</p>
            <p>If progress stalls, consider deloading, changing exercises, or adjusting your training program.</p>
          </div>
          <div>
            <p className="font-medium mb-2">Long-term View</p>
            <p>Strength gains happen over months and years. Focus on sustainable progress rather than quick fixes.</p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
