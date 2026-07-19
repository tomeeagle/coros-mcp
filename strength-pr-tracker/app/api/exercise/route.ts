import { NextRequest, NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import Exercise from '@/lib/models/Exercise';

export const POST = async (req: NextRequest) => {
  try {
    await connectDB();
    
    const { name, description } = await req.json();
    
    // Check if the exercise already exists
    const existingExercise = await Exercise.findOne({ name });
    if (existingExercise) {
      return NextResponse.json(
        { error: 'Exercise already exists' },
        { status: 409 }
      );
    }
    
    // Create new exercise
    const exercise = new Exercise({ name, description });
    await exercise.save();

    return NextResponse.json(exercise, { status: 201 });
  } catch (error) {
    console.error('Error creating exercise:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
};

export const GET = async () => {
  try {
    await connectDB();
    
    const exercises = await Exercise.find({}).sort({ name: 1 });
    return NextResponse.json(exercises);
  } catch (error) {
    console.error('Error fetching exercises:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
};
