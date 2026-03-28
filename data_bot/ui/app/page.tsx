'use client';

import { CopilotChat } from '@copilotkit/react-core/v2';

export default function Home() {
  return (
    <main className="h-screen w-full overflow-hidden bg-gray-950 text-white">
      <div className="flex h-full w-full flex-col bg-gray-800 p-10">
        <CopilotChat
          className="h-full w-full"
          chatView="rounded-xl bg-white text-black p-5"
          labels={{ chatInputPlaceholder: 'Ask me about phones...' }}
        />
      </div>
    </main>
  );
}
