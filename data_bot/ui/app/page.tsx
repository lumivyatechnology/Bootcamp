'use client';

import { CopilotChat } from '@copilotkit/react-ui';


export default function Home() {


  return (
    <main className="h-screen w-full overflow-hidden bg-gray-950 text-white">
      <div className="flex h-full w-full flex-col">
        <CopilotChat
          className="h-full w-full"
          labels={{
            title: 'Copilot',
            initial: 'How can I help you today?',
          }}
        />
      </div>
    </main>
  );
}
