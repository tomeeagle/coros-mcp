import mongoose from 'mongoose';

const SetSchema = new mongoose.Schema({
  weight: {
    type: Number,
    required: true,
    min: 0
  },
  reps: {
    type: Number,
    required: true,
    min: 1
  },
  rpe: {
    type: Number,
    min: 1,
    max: 10,
    required: false
  },
  notes: {
    type: String,
    trim: true
  }
});

const PersonalRecordSchema = new mongoose.Schema({
  exerciseId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Exercise',
    required: true
  },
  date: {
    type: Date,
    required: true,
    default: Date.now
  },
  sets: [SetSchema],
  sessionNotes: {
    type: String,
    trim: true
  },
  totalVolume: {
    type: Number,
    default: 0
  },
  maxWeight: {
    type: Number,
    default: 0
  },
  maxReps: {
    type: Number,
    default: 0
  },
  isPersonalBest: {
    type: Boolean,
    default: false
  },
  pbType: {
    type: String,
    enum: ['weight', 'reps', 'volume', 'none'],
    default: 'none'
  },
  createdAt: {
    type: Date,
    default: Date.now
  },
  updatedAt: {
    type: Date,
    default: Date.now
  }
});

// Calculate totals before saving
PersonalRecordSchema.pre('save', function(next) {
  if (this.sets && this.sets.length > 0) {
    this.totalVolume = this.sets.reduce((total, set) => total + (set.weight * set.reps), 0);
    this.maxWeight = Math.max(...this.sets.map(set => set.weight));
    this.maxReps = Math.max(...this.sets.map(set => set.reps));
  }
  this.updatedAt = new Date();
  next();
});

export default mongoose.models.PersonalRecord || mongoose.model('PersonalRecord', PersonalRecordSchema);
