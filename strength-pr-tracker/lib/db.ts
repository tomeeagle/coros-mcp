import mongoose from 'mongoose';

const MONGODB_URI = process.env.MONGODB_URI;

console.log('MongoDB URI from env:', process.env.MONGODB_URI ? 'SET' : 'NOT SET');
console.log('Using MongoDB URI:', MONGODB_URI ? 'AVAILABLE' : 'NOT AVAILABLE');

if (!MONGODB_URI) {
  throw new Error('Please define the MONGODB_URI environment variable inside .env.local');
}

// TypeScript guard - we know MONGODB_URI is defined after the check above
const MONGODB_URI_SAFE = MONGODB_URI!;

declare global {
  // eslint-disable-next-line no-var
  var mongoose: {
    conn: mongoose.Connection | null;
    promise: Promise<mongoose.Connection> | null;
  } | undefined;
}

let cached = global.mongoose;

if (!cached) {
  cached = global.mongoose = { conn: null, promise: null };
}

// Ensure cached is defined
if (!cached) {
  throw new Error('Failed to initialize mongoose cache');
}

// TypeScript guard to ensure cached is not undefined
const cachedValue = cached!;

export async function connectDB() {
  if (cachedValue.conn) {
    return cachedValue.conn;
  }

  if (!cachedValue.promise) {
    const opts = {
      bufferCommands: false,
    };

    cachedValue.promise = mongoose.connect(MONGODB_URI_SAFE, opts).then((mongoose) => {
      return mongoose.connection;
    });
  }

  try {
    cachedValue.conn = await cachedValue.promise;
  } catch (e) {
    cachedValue.promise = null;
    throw e;
  }

  return cachedValue.conn;
}
