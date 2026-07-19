import { NextRequest, NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import PersonalRecord from '@/lib/models/PersonalRecord';

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    await connectDB();
    
    const { id } = await params;
    const body = await request.json();
    const { weight, reps, date, notes } = body;

    // Validate required fields
    if (weight === undefined || weight === null || weight === '') {
      return NextResponse.json(
        { error: 'Missing required field: weight' },
        { status: 400 }
      );
    }
    
    if (!reps || reps === 0) {
      return NextResponse.json(
        { error: 'Missing required field: reps' },
        { status: 400 }
      );
    }

    // Validate that weight is a valid number
    if (isNaN(parseFloat(weight)) || parseFloat(weight) < 0) {
      return NextResponse.json(
        { error: 'Weight must be a valid number (0 or greater)' },
        { status: 400 }
      );
    }

    const updatedRecord = await PersonalRecord.findByIdAndUpdate(
      id,
      {
        weight: parseFloat(weight),
        reps: parseInt(reps),
        date: date ? new Date(date) : new Date(),
        notes: notes?.trim() || '',
        updatedAt: new Date()
      },
      { new: true }
    );

    if (!updatedRecord) {
      return NextResponse.json(
        { error: 'Personal record not found' },
        { status: 404 }
      );
    }

    return NextResponse.json(updatedRecord);
  } catch (error) {
    console.error('Error updating personal record:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    await connectDB();
    
    const { id } = await params;
    const deletedRecord = await PersonalRecord.findByIdAndDelete(id);
    
    if (!deletedRecord) {
      return NextResponse.json(
        { error: 'Personal record not found' },
        { status: 404 }
      );
    }

    return NextResponse.json(
      { message: 'Personal record deleted successfully' },
      { status: 200 }
    );
  } catch (error) {
    console.error('Error deleting personal record:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
