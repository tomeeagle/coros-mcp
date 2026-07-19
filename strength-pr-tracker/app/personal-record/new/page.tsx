'use client';

import { DashboardLayout } from '@/components/DashboardLayout';
import { ArrowLeft, Plus, Trash2, Activity } from 'lucide-react';
import Link from 'next/link';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface Exercise {
  _id: string;
  name: string;
}

interface Set {
  weight: string;
  reps: string;
  rpe: string;
  notes: string;
}

export default function LogSessionPage() {
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [selectedExercise, setSelectedExercise] = useState('');
  const [sets, setSets] = useState<Set[]>([
    { weight: '', reps: '', rpe: '', notes: '' }
  ]);
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [sessionNotes, setSessionNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingExercises, setIsLoadingExercises] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const fetchExercises = async () => {
      try {
        setIsLoadingExercises(true);
        const res = await fetch('/api/exercise');
        const data = await res.json();
        setExercises(data);
        
        // Check if exercise is pre-selected from URL parameter
        const urlParams = new URLSearchParams(window.location.search);
        const exerciseId = urlParams.get('exercise');
        if (exerciseId && data.some((ex: Exercise) => ex._id === exerciseId)) {
          setSelectedExercise(exerciseId);
        }
      } catch (error) {
        console.error(error);
      } finally {
        setIsLoadingExercises(false);
      }
    };
    fetchExercises();
  }, []);

  const addSet = () => {
    setSets([...sets, { weight: '', reps: '', rpe: '', notes: '' }]);
  };

  const removeSet = (index: number) => {
    if (sets.length > 1) {
      setSets(sets.filter((_, i) => i !== index));
    }
  };

  const updateSet = (index: number, field: keyof Set, value: string) => {
    const newSets = [...sets];
    newSets[index] = { ...newSets[index], [field]: value };
    setSets(newSets);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    // Client-side validation
    if (!selectedExercise) {
      alert('Please select an exercise type');
      setIsSubmitting(false);
      return;
    }
    
    if (sets.length === 0) {
      alert('Please add at least one set');
      setIsSubmitting(false);
      return;
    }

    // Validate all sets
    for (let i = 0; i < sets.length; i++) {
      const set = sets[i];
      if (set.weight === '' || isNaN(parseFloat(set.weight)) || parseFloat(set.weight) < 0) {
        alert(`Set ${i + 1}: Please enter a valid weight (0 or greater for bodyweight exercises)`);
        setIsSubmitting(false);
        return;
      }
      
      if (set.reps === '' || isNaN(parseInt(set.reps)) || parseInt(set.reps) <= 0) {
        alert(`Set ${i + 1}: Please enter a valid number of reps`);
        setIsSubmitting(false);
        return;
      }
    }

    const requestBody = {
      exerciseId: selectedExercise,
      sets: sets.map(set => ({
        weight: parseFloat(set.weight),
        reps: parseInt(set.reps),
        rpe: set.rpe ? parseInt(set.rpe) : null,
        notes: set.notes.trim()
      })),
      date: date,
      sessionNotes: sessionNotes.trim()
    };

    console.log('Submitting session with data:', requestBody);

    try {
      const response = await fetch('/api/personal-record', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      const responseData = await response.json();
      console.log('API response:', responseData);

      if (response.ok) {
        // Show success message with PR details if applicable
        if (responseData.isPersonalBest) {
          alert(`🎉 ${responseData.improvementMessage}`);
        } else {
          alert(`📝 ${responseData.improvementMessage}`);
        }
        
        // Redirect to the exercise detail page to see the new session
        router.push(`/exercises/${selectedExercise}`);
      } else {
        console.error('Failed to log session:', responseData);
        alert(`Error: ${responseData.error || 'Failed to log session'}`);
      }
    } catch (error) {
      console.error('Error logging session:', error);
      alert('An error occurred while submitting the form');
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
            href="/"
            className="mr-4 p-2 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Log Training Session</h1>
        </div>
        <p className="mt-2 text-gray-600">
          Track your complete training session with multiple sets, RPE, and notes.
        </p>
        <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>💡 Session Tracking Benefits:</strong>
          </p>
          <ul className="text-sm text-blue-700 mt-1 ml-4 list-disc">
            <li>Track every set for complete progression history</li>
            <li>Monitor RPE (Rate of Perceived Exertion) for intensity tracking</li>
            <li>Automatic PR detection across all metrics</li>
            <li>Better insights into your training patterns</li>
          </ul>
        </div>
      </div>

      {/* Form Card */}
      <div className="max-w-4xl">
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Exercise Selection */}
            <div>
              <label htmlFor="exercise" className="block text-sm font-medium text-gray-700 mb-2">
                Exercise Type
              </label>
              {isLoadingExercises ? (
                <div className="text-center py-8 border-2 border-dashed border-gray-300 rounded-lg">
                  <div className="text-gray-500 mb-4">
                    <p className="text-lg font-medium mb-2">Loading exercises...</p>
                    <p className="text-sm">Please wait while we fetch the available exercises.</p>
                  </div>
                </div>
              ) : exercises.length === 0 ? (
                <div className="text-center py-8 border-2 border-dashed border-gray-300 rounded-lg">
                  <div className="text-gray-500 mb-4">
                    <p className="text-lg font-medium mb-2">No exercise types available</p>
                    <p className="text-sm">You need to create exercise types before logging sessions</p>
                  </div>
                  <Link
                    href="/exercises/add"
                    className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Exercise Type
                  </Link>
                </div>
              ) : (
                <select
                  id="exercise"
                  value={selectedExercise}
                  onChange={(e) => setSelectedExercise(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  <option value="">Select an exercise type</option>
                  {exercises && exercises.map((exercise) => (
                    <option key={exercise._id} value={exercise._id}>
                      {exercise.name}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Date */}
            <div>
              <label htmlFor="date" className="block text-sm font-medium text-gray-700 mb-2">
                Session Date
              </label>
              <input
                type="date"
                id="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            {/* Sets */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <label className="block text-sm font-medium text-gray-700">
                  Training Sets
                </label>
                <button
                  type="button"
                  onClick={addSet}
                  className="inline-flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors text-sm"
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Add Set
                </button>
              </div>
              
              <div className="space-y-4">
                {sets.map((set, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-sm font-medium text-gray-700">Set {index + 1}</h4>
                      {sets.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeSet(index)}
                          className="p-1 text-red-500 hover:text-red-700 transition-colors"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">Weight (kg)</label>
                        <input
                          type="number"
                          value={set.weight}
                          onChange={(e) => updateSet(index, 'weight', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                          placeholder="0 for bodyweight"
                          step="0.5"
                          min="0"
                          required
                        />
                      </div>
                      
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">Reps</label>
                        <input
                          type="number"
                          value={set.reps}
                          onChange={(e) => updateSet(index, 'reps', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                          placeholder="5"
                          min="1"
                          required
                        />
                      </div>
                      
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">RPE (1-10)</label>
                        <input
                          type="number"
                          value={set.rpe}
                          onChange={(e) => updateSet(index, 'rpe', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                          placeholder="7"
                          min="1"
                          max="10"
                        />
                        <p className="text-xs text-gray-500 mt-1">Rate of Perceived Exertion</p>
                      </div>
                      
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">Notes</label>
                        <input
                          type="text"
                          value={set.notes}
                          onChange={(e) => updateSet(index, 'notes', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                          placeholder="Form, energy, etc."
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Session Notes */}
            <div>
              <label htmlFor="sessionNotes" className="block text-sm font-medium text-gray-700 mb-2">
                Session Notes (Optional)
              </label>
              <textarea
                id="sessionNotes"
                value={sessionNotes}
                onChange={(e) => setSessionNotes(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Overall session notes, energy levels, form observations, etc."
              />
            </div>

            {/* Submit Button */}
            <div className="flex items-center justify-end space-x-4 pt-4">
              <Link
                href="/"
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Cancel
              </Link>
              <button
                type="submit"
                disabled={isSubmitting || !selectedExercise || sets.length === 0 || isLoadingExercises}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
              >
                <Activity className="h-4 w-4 mr-2" />
                {isSubmitting ? 'Logging Session...' : 'Log Session'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </DashboardLayout>
  );
}
