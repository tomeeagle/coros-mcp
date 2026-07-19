import { NextRequest, NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import PersonalRecord from '@/lib/models/PersonalRecord';
import Exercise from '@/lib/models/Exercise';

export async function POST(request: NextRequest) {
  try {
    await connectDB();
    
    const body = await request.json();
    const { exerciseId, sets, date, sessionNotes } = body;

    // Debug logging
    console.log('Received request body:', body);
    console.log('Parsed fields:', { exerciseId, sets, date, sessionNotes });

    // Validate required fields
    if (!exerciseId) {
      console.log('Missing exerciseId');
      return NextResponse.json(
        { error: 'Missing required field: exerciseId' },
        { status: 400 }
      );
    }
    
    if (!sets || !Array.isArray(sets) || sets.length === 0) {
      console.log('Missing or invalid sets:', sets);
      return NextResponse.json(
        { error: 'Missing required field: sets (must be a non-empty array)' },
        { status: 400 }
      );
    }

    // Validate each set
    for (const set of sets) {
      if (set.weight === undefined || set.weight === null || set.weight === '') {
        return NextResponse.json(
          { error: 'Missing weight in set' },
          { status: 400 }
        );
      }
      
      if (!set.reps || set.reps === 0) {
        return NextResponse.json(
          { error: 'Missing or invalid reps in set' },
          { status: 400 }
        );
      }

      // Allow 0 for bodyweight exercises, but ensure it's a valid number
      if (isNaN(parseFloat(set.weight)) || parseFloat(set.weight) < 0) {
        return NextResponse.json(
          { error: 'Weight must be a valid number (0 or greater)' },
          { status: 400 }
        );
      }
    }

    // Validate that exercise exists
    const exercise = await Exercise.findById(exerciseId);
    if (!exercise) {
      console.log('Exercise not found with ID:', exerciseId);
      return NextResponse.json(
        { error: 'Exercise type not found' },
        { status: 404 }
      );
    }

    // Check if this session contains any personal bests
    const existingRecords = await PersonalRecord.find({ exerciseId }).sort({ date: -1 });
    let isPersonalBest = false;
    let pbType = 'none';
    let improvementMessage = '';

    if (existingRecords.length > 0) {
      const latestRecord = existingRecords[0];
      
      // Calculate session totals
      const sessionMaxWeight = Math.max(...sets.map(s => parseFloat(s.weight)));
      const sessionMaxReps = Math.max(...sets.map(s => parseInt(s.reps)));
      const sessionVolume = sets.reduce((total, set) => total + (parseFloat(set.weight) * parseInt(set.reps)), 0);
      
      // Check for weight PR (higher weight with same or more reps)
      if (sessionMaxWeight > latestRecord.maxWeight) {
        isPersonalBest = true;
        pbType = 'weight';
        improvementMessage = `New weight PR! ${sessionMaxWeight} kg (previous: ${latestRecord.maxWeight} kg)`;
      }
      // Check for reps PR (more reps with same or higher weight)
      else if (sessionMaxReps > latestRecord.maxReps && sessionMaxWeight >= latestRecord.maxWeight) {
        isPersonalBest = true;
        pbType = 'reps';
        improvementMessage = `New reps PR! ${sessionMaxReps} reps at ${sessionMaxWeight} kg (previous: ${latestRecord.maxReps} reps)`;
      }
      // Check for volume PR (higher total volume)
      else if (sessionVolume > latestRecord.totalVolume) {
        isPersonalBest = true;
        pbType = 'volume';
        improvementMessage = `New volume PR! ${sessionVolume} total kg (previous: ${latestRecord.totalVolume} total kg)`;
      }
      else {
        improvementMessage = `Good session! Your best is still ${latestRecord.maxWeight} kg × ${latestRecord.maxReps} reps`;
      }
    } else {
      isPersonalBest = true;
      pbType = 'first';
      improvementMessage = `First session for this exercise! Great start!`;
    }

    const personalRecord = new PersonalRecord({
      exerciseId,
      sets: sets.map(set => ({
        weight: parseFloat(set.weight),
        reps: parseInt(set.reps),
        rpe: set.rpe || null,
        notes: set.notes || ''
      })),
      date: date ? new Date(date) : new Date(),
      sessionNotes: sessionNotes?.trim() || '',
      isPersonalBest,
      pbType
    });

    await personalRecord.save();

    return NextResponse.json(
      { 
        message: isPersonalBest ? 'Personal best achieved!' : 'Session logged successfully!',
        record: personalRecord,
        isPersonalBest,
        pbType,
        improvementMessage,
        exerciseName: exercise.name
      },
      { status: 201 }
    );
  } catch (error) {
    console.error('Error adding session:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    await connectDB();
    
    const { searchParams } = new URL(request.url);
    const exerciseId = searchParams.get('exerciseId');
    
    let query = {};
    if (exerciseId) {
      query = { exerciseId };
    }
    
    const personalRecords = await PersonalRecord.find(query)
      .populate('exerciseId', 'name')
      .sort({ date: -1 });
    
    return NextResponse.json(personalRecords);
  } catch (error) {
    console.error('Error fetching sessions:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
