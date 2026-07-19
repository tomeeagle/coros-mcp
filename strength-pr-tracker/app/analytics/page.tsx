'use client';

import { DashboardLayout } from '@/components/DashboardLayout';
import { TrendingUp, Calendar, Target, Activity } from 'lucide-react';
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

export default function AnalyticsPage() {
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [sessions, setSessions] = useState<PersonalRecord[]>([]);
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
        console.error('Error fetching analytics data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const getTotalSessions = () => sessions.length;
  const getTotalVolume = () => sessions.reduce((total, session) => total + session.totalVolume, 0);
  const getTotalSets = () => sessions.reduce((total, session) => total + session.sets.length, 0);
  const getAverageSessionsPerWeek = () => {
    if (sessions.length === 0) return 0;
    const firstSession = new Date(Math.min(...sessions.map(s => new Date(s.date).getTime())));
    const now = new Date();
    const weeksDiff = Math.max(1, Math.ceil((now.getTime() - firstSession.getTime()) / (1000 * 60 * 60 * 24 * 7)));
    return Math.round((sessions.length / weeksDiff) * 10) / 10;
  };

  const getMostTrainedExercise = () => {
    if (sessions.length === 0) return null;
    const exerciseCounts = sessions.reduce((acc, session) => {
      const exerciseName = session.exerciseId.name;
      acc[exerciseName] = (acc[exerciseName] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    const mostTrained = Object.entries(exerciseCounts).sort(([,a], [,b]) => b - a)[0];
    return mostTrained ? { name: mostTrained[0], count: mostTrained[1] } : null;
  };

  const getRecentProgress = () => {
    if (sessions.length < 2) return [];
    
    const sortedSessions = sessions.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    const lastTwo = sortedSessions.slice(-2);
    
    return lastTwo.map((session, index) => {
      const prevSession = index > 0 ? lastTwo[index - 1] : null;
      let progress = '';
      
      if (prevSession) {
        const weightDiff = session.maxWeight - prevSession.maxWeight;
        const repsDiff = session.maxReps - prevSession.maxReps;
        const volumeDiff = session.totalVolume - prevSession.totalVolume;
        
        if (weightDiff > 0) progress += `+${weightDiff}kg weight `;
        if (repsDiff > 0) progress += `+${repsDiff} reps `;
        if (volumeDiff > 0) progress += `+${volumeDiff}kg volume `;
        if (!progress) progress = 'Maintained performance';
      } else {
        progress = 'First session';
      }
      
      return {
        exercise: session.exerciseId.name,
        date: new Date(session.date).toLocaleDateString(),
        progress: progress.trim()
      };
    });
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading analytics...</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Training Analytics</h1>
        <p className="text-gray-600">
          Track your training progress, volume, and performance trends
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Activity className="h-5 w-5 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Sessions</p>
              <p className="text-2xl font-bold text-gray-900">{getTotalSessions()}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <TrendingUp className="h-5 w-5 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Volume</p>
              <p className="text-2xl font-bold text-gray-900">{getTotalVolume().toLocaleString()} kg</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Target className="h-5 w-5 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Sets</p>
              <p className="text-2xl font-bold text-gray-900">{getTotalSets()}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <div className="flex items-center">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Calendar className="h-5 w-5 text-orange-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Sessions/Week</p>
              <p className="text-2xl font-bold text-gray-900">{getAverageSessionsPerWeek()}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Training Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Most Trained Exercise */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Most Trained Exercise</h3>
          {getMostTrainedExercise() ? (
            <div className="text-center py-8">
              <Target className="h-16 w-16 text-blue-600 mx-auto mb-4" />
              <h4 className="text-2xl font-bold text-gray-900 mb-2">
                {getMostTrainedExercise()!.name}
              </h4>
              <p className="text-lg text-gray-600">
                {getMostTrainedExercise()!.count} training sessions
              </p>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>No training data yet</p>
            </div>
          )}
        </div>

        {/* Recent Progress */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Progress</h3>
          {getRecentProgress().length > 0 ? (
            <div className="space-y-4">
              {getRecentProgress().map((progress, index) => (
                <div key={index} className="border-l-4 border-blue-500 pl-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900">{progress.exercise}</p>
                      <p className="text-sm text-gray-600">{progress.date}</p>
                    </div>
                    <span className="text-sm text-blue-600 font-medium">{progress.progress}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>No recent progress data</p>
            </div>
          )}
        </div>
      </div>

      {/* Exercise Breakdown */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm mb-8">
        <h3 className="text-lg font-medium text-gray-900 mb-6">Exercise Breakdown</h3>
        {exercises.length > 0 ? (
          <div className="space-y-4">
            {exercises.map((exercise) => {
              const exerciseSessions = sessions.filter(s => s.exerciseId._id === exercise._id);
              const totalVolume = exerciseSessions.reduce((total, s) => total + s.totalVolume, 0);
              const sessionCount = exerciseSessions.length;
              const maxWeight = exerciseSessions.length > 0 ? Math.max(...exerciseSessions.map(s => s.maxWeight)) : 0;
              const maxReps = exerciseSessions.length > 0 ? Math.max(...exerciseSessions.map(s => s.maxReps)) : 0;
              
              return (
                <div key={exercise._id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-lg font-medium text-gray-900">{exercise.name}</h4>
                    <Link
                      href={`/exercises/${exercise._id}`}
                      className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                    >
                      View Details →
                    </Link>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-gray-600">Sessions</p>
                      <p className="font-medium text-gray-900">{sessionCount}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Total Volume</p>
                      <p className="font-medium text-gray-900">{totalVolume.toLocaleString()} kg</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Max Weight</p>
                      <p className="font-medium text-gray-900">{maxWeight} kg</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Max Reps</p>
                      <p className="font-medium text-gray-900">{maxReps}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <p>No exercise types created yet</p>
            <Link href="/exercises/add" className="text-blue-600 hover:underline mt-2 inline-block">
              Create your first exercise type
            </Link>
          </div>
        )}
      </div>

      {/* Training Tips */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl border border-blue-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">💡 Analytics Insights</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-700">
          <div>
            <p className="font-medium mb-2">Volume Tracking</p>
            <p>Total volume (weight × reps) is a key metric for tracking overall training load and progress.</p>
          </div>
          <div>
            <p className="font-medium mb-2">Frequency Analysis</p>
            <p>Regular training sessions are more effective than sporadic intense workouts for long-term progress.</p>
          </div>
          <div>
            <p className="font-medium mb-2">Exercise Variety</p>
            <p>Balancing different movement patterns ensures comprehensive strength development and injury prevention.</p>
          </div>
          <div>
            <p className="font-medium mb-2">Progress Monitoring</p>
            <p>Track both weight and reps to identify plateaus and adjust your training program accordingly.</p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
