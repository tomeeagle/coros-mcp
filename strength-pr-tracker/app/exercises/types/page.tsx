'use client';

import { DashboardLayout } from '@/components/DashboardLayout';
import { Plus, Target, Dumbbell, Activity, TrendingUp, Calendar } from 'lucide-react';
import Link from 'next/link';
import { useState, useEffect } from 'react';

interface Exercise {
  _id: string;
  name: string;
  description?: string;
  createdAt: string;
}

export default function ExerciseTypesPage() {
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchExercises = async () => {
      try {
        setIsLoading(true);
        const response = await fetch('/api/exercise');
        const data = await response.json();
        setExercises(data);
      } catch (error) {
        console.error('Error fetching exercises:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchExercises();
  }, []);

  const getExerciseIcon = (exerciseName: string) => {
    const name = exerciseName.toLowerCase();
    
    if (name.includes('push') || name.includes('press') || name.includes('bench')) {
      return <Dumbbell className="h-6 w-6" />;
    } else if (name.includes('pull') || name.includes('row') || name.includes('chin')) {
      return <Target className="h-6 w-6" />;
    } else if (name.includes('squat') || name.includes('leg') || name.includes('dead')) {
      return <TrendingUp className="h-6 w-6" />;
    } else if (name.includes('curl') || name.includes('extension') || name.includes('raise')) {
      return <Activity className="h-6 w-6" />;
    } else {
      return <Target className="h-6 w-6" />;
    }
  };

  const getIconBgColor = (exerciseName: string) => {
    const name = exerciseName.toLowerCase();
    
    if (name.includes('push') || name.includes('press') || name.includes('bench')) {
      return 'bg-blue-100 text-blue-600';
    } else if (name.includes('pull') || name.includes('row') || name.includes('chin')) {
      return 'bg-green-100 text-green-600';
    } else if (name.includes('squat') || name.includes('leg') || name.includes('dead')) {
      return 'bg-purple-100 text-purple-600';
    } else if (name.includes('curl') || name.includes('extension') || name.includes('raise')) {
      return 'bg-orange-100 text-orange-600';
    } else {
      return 'bg-gray-100 text-gray-600';
    }
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading exercise types...</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      {/* Header */}
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Exercise Types</h1>
            <p className="text-gray-600">
              Manage your exercise library and track progress for each movement pattern
            </p>
          </div>
          <div className="mt-4 sm:mt-0">
            <Link
              href="/exercises/add"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Exercise Type
            </Link>
          </div>
        </div>
      </div>

      {/* Exercise Grid */}
      {exercises.length === 0 ? (
        <div className="text-center py-16">
          <Target className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-medium text-gray-900 mb-2">No exercise types yet</h3>
          <p className="text-gray-600 mb-6">
            Create your first exercise type to start tracking your training sessions
          </p>
          <Link
            href="/exercises/add"
            className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="h-5 w-5 mr-2" />
            Create First Exercise Type
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {exercises.map((exercise) => (
            <div key={exercise._id} className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
              {/* Exercise Card Content */}
              <Link href={`/exercises/${exercise._id}`} className="block p-6 hover:bg-gray-50 transition-colors">
                <div className="flex items-start space-x-4">
                  <div className={`p-3 rounded-lg ${getIconBgColor(exercise.name)}`}>
                    {getExerciseIcon(exercise.name)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-semibold text-gray-900 mb-1 truncate">
                      {exercise.name}
                    </h3>
                    {exercise.description && (
                      <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                        {exercise.description}
                      </p>
                    )}
                    <div className="flex items-center text-xs text-gray-500">
                      <Calendar className="h-3 w-3 mr-1" />
                      Created {new Date(exercise.createdAt).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              </Link>
              
              {/* Action Buttons */}
              <div className="px-6 pb-6">
                <div className="flex space-x-3">
                  <Link
                    href={`/personal-record/new?exercise=${exercise._id}`}
                    className="flex-1 inline-flex items-center justify-center px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors text-sm font-medium"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Log Session
                  </Link>
                  <Link
                    href={`/exercises/${exercise._id}`}
                    className="flex-1 inline-flex items-center justify-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium"
                  >
                    <TrendingUp className="h-4 w-4 mr-2" />
                    View Progress
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Exercise Categories Info */}
      <div className="mt-12 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl border border-blue-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">💡 Exercise Categories</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-700">
          <div>
            <p className="font-medium mb-2 text-blue-700">Push Movements</p>
            <p>Bench press, overhead press, push-ups. Focus on chest, shoulders, and triceps.</p>
          </div>
          <div>
            <p className="font-medium mb-2 text-green-700">Pull Movements</p>
            <p>Rows, pull-ups, deadlifts. Target back, biceps, and posterior chain.</p>
          </div>
          <div>
            <p className="font-medium mb-2 text-purple-700">Leg Movements</p>
            <p>Squats, lunges, leg press. Build lower body strength and power.</p>
          </div>
          <div>
            <p className="font-medium mb-2 text-orange-700">Isolation Exercises</p>
            <p>Curls, extensions, raises. Isolate specific muscle groups for targeted growth.</p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
