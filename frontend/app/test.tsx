'use client';
import { useState } from 'react';

export default function Test() {
  const [count, setCount] = useState<number>(0);

  return (
    <div className="flex flex-col items-center gap-4">
      <h1 className="text-2xl">Counter: {count}</h1>
      <div className="flex gap-2">
        <button
          className="rounded bg-blue-500 px-4 py-2 font-bold text-white hover:bg-blue-700"
          onClick={() => setCount(count - 1)}
        >
          Decrement
        </button>
        <button
          className="rounded bg-green-500 px-4 py-2 font-bold text-white hover:bg-green-700"
          onClick={() => setCount(count + 1)}
        >
          Increment
        </button>
      </div>
    </div>
  );
}
