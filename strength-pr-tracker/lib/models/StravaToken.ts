import mongoose from 'mongoose';

const StravaTokenSchema = new mongoose.Schema({
  userId: {
    type: String,
    required: true,
    unique: true
  },
  accessToken: {
    type: String,
    required: true
  },
  refreshToken: {
    type: String,
    required: true
  },
  expiresAt: {
    type: Date,
    required: true
  },
  athleteId: {
    type: Number,
    required: true
  },
  athleteName: {
    type: String,
    required: true
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

// Check if token is expired
StravaTokenSchema.methods.isExpired = function() {
  return new Date() > this.expiresAt;
};

// Check if token expires soon (within 1 hour)
StravaTokenSchema.methods.expiresSoon = function() {
  const oneHourFromNow = new Date();
  oneHourFromNow.setHours(oneHourFromNow.getHours() + 1);
  return this.expiresAt < oneHourFromNow;
};

export default mongoose.models.StravaToken || mongoose.model('StravaToken', StravaTokenSchema);
