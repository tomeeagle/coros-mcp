'use client';

import { DashboardLayout } from '@/components/DashboardLayout';
import { ArrowLeft, Plus, Edit, Trash2, Calendar, Target, TrendingUp, Activity } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useState, useEffect } from 'react';
import { ResponsiveContainer, AreaChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

interface Exercise {
  _id: string;
  name: string;
  description?: string;
}

interface Set {
  weight: number;
  reps: number;
  rpe?: number;
  notes?: string;
}

interface PersonalRecord {
  _id: string;
  exerciseId: string;
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

export default function ExerciseDetailPage() {
  const params = useParams();
  const exerciseId = params.id as string;
  
  const [exercise, setExercise] = useState<Exercise | null>(null);
  const [personalRecords, setPersonalRecords] = useState<PersonalRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        
        // Fetch exercise details
        const exerciseRes = await fetch(`/api/exercise/${exerciseId}`);
        const exerciseData = await exerciseRes.json();
        setExercise(exerciseData);
        
        // Fetch personal records
        const recordsRes = await fetch(`/api/personal-record?exerciseId=${exerciseId}`);
        const recordsData = await recordsRes.json();
        setPersonalRecords(recordsData);
        
        console.log('Exercise:', exerciseData);
        console.log('Personal Records:', recordsData);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    if (exerciseId) {
      fetchData();
    }
  }, [exerciseId]);

  const handleDelete = async (recordId: string) => {
    if (!confirm('Are you sure you want to delete this session?')) {
      return;
    }

    setIsDeleting(recordId);
    try {
      const response = await fetch(`/api/personal-record/${recordId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setPersonalRecords(records => records.filter(r => r._id !== recordId));
      } else {
        alert('Failed to delete session');
      }
    } catch (error) {
      console.error('Error deleting session:', error);
      alert('Error deleting session');
    } finally {
      setIsDeleting(null);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getChartData = () => {
    if (!personalRecords.length) return [];
    
    return personalRecords
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
      .map(record => ({
        date: formatDate(record.date),
        weight: record.maxWeight,
        reps: record.maxReps,
        volume: record.totalVolume,
        sets: record.sets.length
      }));
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading exercise details...</p>
        </div>
      </DashboardLayout>
    );
  }

  if (!exercise) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <p className="text-gray-600">Exercise not found</p>
          <Link href="/exercises/types" className="text-blue-600 hover:underline mt-2 inline-block">
            Back to Exercise Types
          </Link>
        </div>
      </DashboardLayout>
    );
  }

  const chartData = getChartData();
  const hasWeightedSets = personalRecords.some(record => record.sets.some(set => set.weight > 0));

  return (
    <DashboardLayout>
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center mb-4">
          <Link
            href="/exercises/types"
            className="mr-4 p-2 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{exercise.name}</h1>
            {exercise.description && (
              <p className="mt-2 text-gray-600">{exercise.description}</p>
            )}
          </div>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-4">
          <Link
            href={`/personal-record/new?exercise=${exerciseId}`}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="h-4 w-4 mr-2" />
            Log New Session
          </Link>
          
          <Link
            href="/exercises/types"
            className="inline-flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <Target className="h-4 w-4 mr-2" />
            All Exercise Types
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      {personalRecords.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Target className="h-5 w-5 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Sessions</p>
                <p className="text-2xl font-bold text-gray-900">{personalRecords.length}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <TrendingUp className="h-5 w-5 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Max Weight</p>
                <p className="text-2xl font-bold text-gray-900">
                  {Math.max(...personalRecords.map(r => r.maxWeight))} kg
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Activity className="h-5 w-5 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Max Reps</p>
                <p className="text-2xl font-bold text-gray-900">
                  {Math.max(...personalRecords.map(r => r.maxReps))}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <div className="flex items-center">
              <div className="p-2 bg-orange-100 rounded-lg">
                <TrendingUp className="h-5 w-5 text-orange-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Best Volume</p>
                <p className="text-2xl font-bold text-gray-900">
                  {Math.max(...personalRecords.map(r => r.totalVolume))} kg
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Charts */}
      {personalRecords.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm mb-8">
          <h3 className="text-lg font-medium text-gray-900 mb-6">Progress Charts</h3>
          
          <div className="space-y-8">
            {/* Weight Progress Chart - Only show for weighted exercises */}
            {hasWeightedSets && (
              <div>
                <h4 className="text-md font-medium text-gray-700 mb-3">Weight Progress</h4>
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis label={{ value: 'Weight (kg)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip formatter={(value) => [`${value} kg`, 'Weight']} />
                    <Legend />
                    <Line type="monotone" dataKey="weight" stroke="#3b82f6" strokeWidth={2} fill="#3b82f6" fillOpacity={0.1} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Reps Progress Chart - Always show */}
            <div>
              <h4 className="text-md font-medium text-gray-700 mb-3">Reps Progress</h4>
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis label={{ value: 'Reps', angle: -90, position: 'insideLeft' }} />
                  <Tooltip formatter={(value) => [value, 'Reps']} />
                  <Legend />
                  <Line type="monotone" dataKey="reps" stroke="#8b5cf6" strokeWidth={2} fill="#8b5cf6" fillOpacity={0.1} />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Combined Progress Chart - Only show for weighted exercises */}
            {hasWeightedSets && (
              <div>
                <h4 className="text-md font-medium text-gray-700 mb-3">Volume Progress</h4>
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis label={{ value: 'Volume (kg)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip formatter={(value) => [`${value} kg`, 'Volume']} />
                    <Legend />
                    <Line type="monotone" dataKey="volume" stroke="#f97316" strokeWidth={2} fill="#f97316" fillOpacity={0.1} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Bodyweight Exercise Note */}
            {!hasWeightedSets && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-blue-800">Bodyweight Exercise</h3>
                    <p className="text-sm text-blue-700 mt-1">
                      This is a bodyweight exercise, so weight progress isn&apos;t tracked. Focus on improving your reps and overall performance!
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Sessions List */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-medium text-gray-900">Training Sessions</h3>
          <span className="text-sm text-gray-500">{personalRecords.length} sessions</span>
        </div>

        {personalRecords.length === 0 ? (
          <div className="text-center py-12">
            <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No sessions yet</h3>
            <p className="text-gray-600 mb-6">Start tracking your progress by logging your first training session.</p>
            <Link
              href={`/personal-record/new?exercise=${exerciseId}`}
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="h-4 w-4 mr-2" />
              Log First Session
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {personalRecords
              .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
              .map((record) => (
                <div key={record._id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-3">
                        <Calendar className="h-4 w-4 text-gray-400" />
                        <span className="text-sm font-medium text-gray-900">
                          {formatDate(record.date)}
                        </span>
                        {record.isPersonalBest && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            🎉 {record.pbType === 'weight' ? 'Weight PR' : 
                                 record.pbType === 'reps' ? 'Reps PR' : 
                                 record.pbType === 'volume' ? 'Volume PR' : 'First Session'}
                          </span>
                        )}
                      </div>
                      
                      {/* Sets Display */}
                      <div className="space-y-2 mb-3">
                        {record.sets.map((set, index) => (
                          <div key={index} className="flex items-center space-x-4 text-sm">
                            <span className="text-gray-500 min-w-[60px]">Set {index + 1}:</span>
                            <span className="font-medium">{set.weight} kg × {set.reps} reps</span>
                            {set.rpe && (
                              <span className="text-gray-500">RPE {set.rpe}</span>
                            )}
                                                         {set.notes && (
                               <span className="text-gray-500 italic">&quot;{set.notes}&quot;</span>
                             )}
                          </div>
                        ))}
                      </div>
                      
                      {/* Session Summary */}
                      <div className="flex items-center space-x-6 text-sm text-gray-600">
                        <span>Total Volume: <strong>{record.totalVolume} kg</strong></span>
                        <span>Max Weight: <strong>{record.maxWeight} kg</strong></span>
                        <span>Max Reps: <strong>{record.maxReps}</strong></span>
                        <span>Sets: <strong>{record.sets.length}</strong></span>
                      </div>
                      
                      {record.sessionNotes && (
                                                 <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                           <p className="text-sm text-gray-700 italic">&quot;{record.sessionNotes}&quot;</p>
                         </div>
                      )}
                    </div>
                    
                    <div className="flex items-center space-x-2 ml-4">
                      <Link
                        href={`/personal-record/${record._id}/edit`}
                        className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                      >
                        <Edit className="h-4 w-4" />
                      </Link>
                      <button
                        onClick={() => handleDelete(record._id)}
                        disabled={isDeleting === record._id}
                        className="p-2 text-gray-400 hover:text-red-600 transition-colors disabled:opacity-50"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
