'use client';

import { DashboardLayout } from '@/components/DashboardLayout';
import { ArrowLeft, Target } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function AddExercisePage() {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const response = await fetch('/api/exercise', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, description }),
      });

      const responseData = await response.json();
      console.log('API response:', responseData);

      if (response.ok) {
        alert('Exercise type created successfully!');
        router.push('/exercises/types');
      } else {
        console.error('Failed to create exercise:', responseData);
        alert(`Error: ${responseData.error || 'Failed to create exercise type'}`);
      }
    } catch (error) {
      console.error('Error creating exercise:', error);
      alert('An error occurred while creating the exercise type');
    } finally {
      setIsSubmitting(false);
    }
  };

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
          <h1 className="text-3xl font-bold text-gray-900">Add Exercise Type</h1>
        </div>
        <p className="mt-2 text-gray-600">
          Create a new exercise type to start tracking your training sessions
        </p>
      </div>

      {/* Form Card */}
      <div className="max-w-2xl">
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Exercise Name */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                Exercise Name
              </label>
              <input
                type="text"
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., Bench Press, Squat, Pull-up"
                required
              />
              <p className="mt-1 text-sm text-gray-500">
                Use descriptive names that clearly identify the movement pattern
              </p>
            </div>

            {/* Description */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                Description (Optional)
              </label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Brief description of the exercise, target muscles, or any specific notes..."
              />
              <p className="mt-1 text-sm text-gray-500">
                Helpful for organizing your exercise library and remembering form cues
              </p>
            </div>

            {/* Exercise Examples */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-sm font-medium text-blue-800 mb-3">💡 Exercise Examples</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-700">
                <div>
                  <p className="font-medium">Compound Movements</p>
                  <p>Bench Press, Squat, Deadlift, Pull-up, Overhead Press</p>
                </div>
                <div>
                  <p className="font-medium">Isolation Exercises</p>
                  <p>Bicep Curl, Tricep Extension, Lateral Raise, Leg Extension</p>
                </div>
                <div>
                  <p className="font-medium">Bodyweight</p>
                  <p>Push-up, Pull-up, Dip, Lunge, Plank</p>
                </div>
                <div>
                  <p className="font-medium">Cardio/Endurance</p>
                  <p>Running, Cycling, Rowing, Swimming, Jump Rope</p>
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex items-center justify-end space-x-4 pt-4">
              <Link
                href="/exercises/types"
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Cancel
              </Link>
              <button
                type="submit"
                disabled={isSubmitting || !name.trim()}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
              >
                <Target className="h-4 w-4 mr-2" />
                {isSubmitting ? 'Creating...' : 'Create Exercise Type'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </DashboardLayout>
  );
}
